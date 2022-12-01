import os
from datetime import datetime
from typing import Union

import discourse

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from fastapi import Depends, FastAPI, HTTPException, Request, Header, Cookie, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from starlette.responses import FileResponse

from app.db import User, create_db_and_tables
from app.schemas import UserCreate, UserRead, UserUpdate
from app.users import auth_backend, current_active_user, fastapi_users
from app.discoursesso import DiscourseSSO


ACCOUNT_FILE_SIZE_LIMIT_BYTES = 100_000_000
ACCOUNTS_BUCKET = 'lazybug-accounts'
LOCAL_ONLY = os.getenv('LOCAL_ONLY') is not None
DISCOURSE_SECRET, ENDPOINT, KEY_ID, APPLICATION_KEY = None, None, None, None
if not LOCAL_ONLY:
    ENDPOINT = os.getenv('B2_ENDPOINT')
    KEY_ID = os.getenv('B2_APPLICATION_KEY_ID')
    APPLICATION_KEY = os.getenv('B2_APPLICATION_KEY')
    DISCOURSE_SECRET = os.getenv('DISCOURSE_SECRET')
    DISCOURSE_API_KEY = os.getenv('DISCOURSE_API_KEY')
    discourse_client = discourse.Client(
        host='http://discourse.lazybug.ai/',
        api_username='system',
        api_key=DISCOURSE_API_KEY,
    )

if not LOCAL_ONLY and (ENDPOINT is None or KEY_ID is None or APPLICATION_KEY is None):
    print('ERROR: B2 secrets not set')
    exit(1)

def get_b2_resource(endpoint, key_id, application_key):
    b2 = boto3.resource(
        service_name='s3',
        endpoint_url=endpoint,     # Backblaze endpoint
        aws_access_key_id=key_id,  # Backblaze keyID
        aws_secret_access_key=application_key, # Backblaze applicationKey
        config=Config(signature_version='s3v4')
    )
    return b2

b2 = get_b2_resource(ENDPOINT, KEY_ID, APPLICATION_KEY)

app = FastAPI()
client = TestClient(app)

app.mount("/static", StaticFiles(directory="modules/lazyweb"), name="static")

app.mount("/cdn/lazybug-public", StaticFiles(directory="data/remote/public"), name="cdn")

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/api/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/api/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/api/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/api/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/api/users",
    tags=["users"],
)


@app.on_event("startup")
async def on_startup():
    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()


def get_account_file(user):
    return f'{user.email}.json'


@app.get("/api/signed-upload-link/{size}")
async def get_signed_upload_link(size:int, user: User = Depends(current_active_user)):
    if size > ACCOUNT_FILE_SIZE_LIMIT_BYTES:
        raise HTTPException(status_code=400, detail=f'Payload too large, > {ACCOUNT_FILE_SIZE_LIMIT_BYTES/10e6} Mb')

    if LOCAL_ONLY:
        url = '/api/upload-file'
    else:
        url = b2.meta.client.generate_presigned_url(
            ClientMethod='put_object',
            Params={'Bucket': ACCOUNTS_BUCKET, 'Key': get_account_file(user)},
            ExpiresIn=120
        )

    return url


@app.get("/api/signed-download-link")
async def get_signed_download_link(user: User = Depends(current_active_user)):
    key = f'{user.email}.json'

    if LOCAL_ONLY:
        return '/api/download-file/'
    else:
        url = b2.meta.client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': 'lazybug-accounts', 'Key': key},
            ExpiresIn=120
        )

    return url


@app.get("/api/database-last-modified-date")
async def get_database_last_modified_date(user: User = Depends(current_active_user)):
    account_file = get_account_file(user)
    if LOCAL_ONLY:
        path = f'backend/{account_file}'
        if not os.path.exists(path):
            return None
        return datetime.utcfromtimestamp(os.stat(path).st_mtime).strftime('%Y-%m-%d %H:%M:%S')

    try:
        response = b2.meta.client.head_object(Bucket=ACCOUNTS_BUCKET, Key=account_file)
    except ClientError:
        # No such account file yet
        return None

    if response['ContentLength'] > ACCOUNT_FILE_SIZE_LIMIT_BYTES:
        # User used the signed upload link to upload a too large file, so we delete it and raise 404
        print(f'{user.email} account file too large ({response["ContentLength"] / 10e6} Mb), deleting')
        b2.meta.client.delete_object(Bucket=ACCOUNTS_BUCKET, Key=account_file)
        raise HTTPException(status_code=404, detail=f'File does not exist')

    return response["LastModified"]

if LOCAL_ONLY:
    @app.put("/api/upload-file")
    async def upload_file(request: Request, user: User = Depends(current_active_user)):
        body = await request.body()
        account_file = get_account_file(user)
        path = f'backend/{account_file}'
        with open(path, 'wb') as f:
            f.write(body)
else:
    @app.get("/api/discourse/get-id-and-email")
    async def discourse_get_email_and_id(user: User = Depends(current_active_user)):
        return [user.id, user.email]


    @app.get("/api/discourse/sso")
    async def discourse_sso(sso, sig, jwt = Cookie(default=None)):
        """
        When user enters discourse.lazybug.ai, Discourse calls this endpoint on lazybug.ai server
        with sso and sig tokens. We check the cookies for the jwt token set on lazybug.ai
        (user has to have logged in there first), and return the associated user id and email of the account
        """
        if jwt is None:
            raise HTTPException(status_code=403, detail=f'No jwt token')

        # Get jwt from cookies, then do a local request to get the email
        headers = {'Authorization': 'Bearer ' + jwt}
        user_id, user_email = client.get('/api/discourse/get-id-and-email', headers=headers).json()

        credentials = {
            "external_id" : user_id,
            "email" : user_email,
        }

        discourse = DiscourseSSO(DISCOURSE_SECRET)

        if discourse.validate(sso, sig):
            # Get users login credentials and build the URL to log the user
            # into your discourse site. ex: discourse.example.com
            credentials['nonce'] = discourse.get_nonce(sso)
            return_url_base = "https://discourse.lazybug.ai/session/sso_login?%s"
            return_url =  return_url_base % discourse.build_login_URL(credentials)
            print(credentials)
            return RedirectResponse(return_url)

        raise HTTPException(status_code=403, detail=f'Discourse SSO failed')


    @app.get("/api/discourse/comments/{topic_id}")
    async def discourse_topic_comments(topic_id: int, response: Response):
        response.headers['Cache-Control'] = 'max-age=300'  # cache for 5 minutes

        try:
            topic = discourse_client.get_topic(topic_id)
        except:
            raise HTTPException(status_code=404, detail='Topic does not exist')

        posts = []
        for post in topic.post_stream['posts']:
            post_data = {
                text: post['cooked'],
                created_at: post['created_at'],
                username: post['username'],
            }
            posts.append(post_data)

        return posts


# NOTE: need to put this last!
@app.get("/{rest_of_path:path}")
async def read_index():
    return FileResponse('modules/lazyweb/index.html')
