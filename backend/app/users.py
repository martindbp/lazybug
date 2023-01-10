import os
import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi_mail.schemas import MessageType
from app.db import User, get_user_db


LAZYBUG_SECRET = os.getenv('LAZYBUG_SECRET')
LAZYBUG_SMTP_ADDRESS = os.getenv('LAZYBUG_SMTP_ADDRESS')
LAZYBUG_SMTP_PORT = os.getenv('LAZYBUG_SMTP_PORT')
LAZYBUG_SMTP_USER_NAME = os.getenv('LAZYBUG_SMTP_USER_NAME')
LAZYBUG_SMTP_PASSWORD = os.getenv('LAZYBUG_SMTP_PASSWORD')
LAZYBUG_NOTIFICATION_EMAIL = os.getenv('LAZYBUG_NOTIFICATION_EMAIL')

conf = ConnectionConfig(
    MAIL_USERNAME = LAZYBUG_SMTP_USER_NAME,
    MAIL_PASSWORD = LAZYBUG_SMTP_PASSWORD,
    MAIL_FROM = LAZYBUG_NOTIFICATION_EMAIL,
    MAIL_PORT = LAZYBUG_SMTP_PORT,
    MAIL_SERVER = LAZYBUG_SMTP_ADDRESS,
    MAIL_FROM_NAME="Lazybug Admin",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = LAZYBUG_SECRET
    verification_token_secret = LAZYBUG_SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

        html = f'<p>To reset your password, copy paste the following code:</p><br><p>{token}"></p>'

        message = MessageSchema(
            subject="Lazybug Password Reset Code ",
            recipients=[user.email],
            body=html,
            subtype=MessageType.html)

        fm = FastMail(conf)
        await fm.send_message(message)

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=LAZYBUG_SECRET, lifetime_seconds=None)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
