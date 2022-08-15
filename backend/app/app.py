import os
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from app.db import User, create_db_and_tables
from app.schemas import UserCreate, UserRead, UserUpdate
from app.users import auth_backend, current_active_user, fastapi_users

ENDPOINT = os.getenv('B2_ENDPOINT')
KEY_ID = os.getenv('B2_KEY_ID')
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

app.mount("/static", StaticFiles(directory="frontend/dist"), name="static")

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


@app.get("/")
async def read_index():
    return FileResponse('frontend/dist/index.html')


@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}


@app.on_event("startup")
async def on_startup():
    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()


@app.get("/signed-upload-link")
async def get_signed_upload_link(user: User = Depends(current_active_user)):
    url = b2.meta.client.generate_presigned_url(
        ClientMethod='put_object',
        Params={'Bucket': 'lazybug-accounts', 'Key': f'{user.email}.json'},
        ExpiresIn=1000
    )
    return url

@app.get("/signed-download-link")
async def get_signed_download_link(user: User = Depends(current_active_user)):
    url = b2.meta.client.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': 'lazybug-accounts', 'Key': f'{user.email}.json'},
        ExpiresIn=1000
    )
    return url
