from datetime import timedelta, datetime, timezone
from typing import Annotated

import jwt
from fastapi import HTTPException, Depends, Form
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.auth.schemas import TokenData
from src.core import config, db_helper
from src.users import crud
from src.users.schemas import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/jwt/login",
)

pwd_context = CryptContext(schemes=['argon2'], deprecated='auto')

auth_jwt_config = config.AuthJWT()


def encode_jwt(
    payload: dict,
    private_key: str = auth_jwt_config.private_key,
    algorithm: str = auth_jwt_config.algorithm,
    expire_minutes: int = auth_jwt_config.access_token_expire_minutes,
    expires_delta: timedelta | None = None,
):
    to_encode = payload.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire_time = now + expires_delta
    else:
        expire_time = now + timedelta(minutes=expire_minutes)

    # to_encode.update(
    #     exp=expire_time,
    #     iat=now,
    #     jti=str(uuid.uuid4()),
    # )
    to_encode.update({"exp": expire_time})
    encoded_jwt = jwt.encode(
        payload=to_encode,
        key=private_key,
        algorithm=algorithm,
    )
    return encoded_jwt


def decode_jwt(
    token: str,
    public_key: str = auth_jwt_config.public_key,
    algorithm: str = auth_jwt_config.algorithm,
):
    try:
        return jwt.decode(jwt=token, key=public_key, algorithms=[algorithm])
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token."
        )


def hash_password(password: str) -> str:
    return pwd_context.hash(secret=password)


def validate_password_hash(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(secret=password, hash=hashed_password)


async def get_token_payload(
    token: str = Depends(oauth2_scheme),
):
    try:
        return decode_jwt(token=token)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: AsyncSession = Depends(db_helper.scoped_session_dependency)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            auth_jwt_config.public_key,
            algorithms=[auth_jwt_config.algorithm])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = await crud.get_user_by_username(session=session, username=username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def validate_auth_user(
    username: str = Form(),
    password: str = Form(),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    user = await crud.get_user_by_username(session, username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )

    if not validate_password_hash(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive.",
        )

    return user
