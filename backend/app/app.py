import os
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from app.db import User, create_db_and_tables
from app.schemas import UserCreate, UserRead, UserUpdate
from app.users import auth_backend, current_active_user, fastapi_users

ACCOUNT_FILE_SIZE_LIMIT_BYTES = 100_000_000
ACCOUNTS_BUCKET = 'lazybug-accounts'
ENDPOINT = os.getenv('B2_ENDPOINT')
KEY_ID = os.getenv('B2_APPLICATION_KEY_ID')
APPLICATION_KEY = os.getenv('B2_APPLICATION_KEY')


if ENDPOINT is None or KEY_ID is None or APPLICATION_KEY is None:
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

app.mount("/static", StaticFiles(directory="frontend/lazyweb"), name="static")

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
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

    url = b2.meta.client.generate_presigned_url(
        ClientMethod='put_object',
        Params={'Bucket': ACCOUNTS_BUCKET, 'Key': get_account_file(user)},
        ExpiresIn=120
    )

    return url


@app.get("/api/signed-download-link")
async def get_signed_download_link(user: User = Depends(current_active_user)):
    key = f'{user.email}.json'
    url = b2.meta.client.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': 'lazybug-accounts', 'Key': key},
        ExpiresIn=120
    )
    return url


@app.get("/api/database-last-modified-date")
async def get_database_last_modified_date(user: User = Depends(current_active_user)):
    account_file = get_account_file(user)
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


@app.get("/{rest_of_path:path}")
async def read_index():
    return FileResponse('frontend/lazyweb/index.html')
