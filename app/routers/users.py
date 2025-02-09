"""
API routing for users.
"""
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import timedelta
from typing import Annotated
from pydantic import ValidationError
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import SecurityScopes, OAuth2PasswordRequestForm
from sqlmodel import Field, SQLModel, JSON
from ..errors import Error, ErrorType
from ..db import SessionDep
from ..auth import (
    TokenDep, Token, TokenData,
    verify_password, create_access_token,
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
)

class UserData(SQLModel):
    """
    A single user's data.
    """
    id: str = Field(primary_key=True)
    name: str | None = Field(default=None, nullable=True, index=True,
        min_length=1)
    email: str | None = Field(default=None, nullable=True, index=True,
        min_length=1)
    status: str = Field(default="active")
    data: dict | None = Field(default=None, nullable=True, sa_type=JSON)

class User(UserData, table=True):
    """
    A single user.
    """

    scopes: list[str] | None = Field(default=None, nullable=True, sa_type=JSON)
    hashed_password: str | None

router = APIRouter(
    prefix="/user",
    tags=["user"],
)

def get_user(id: str, session: SessionDep) -> User | None:
    """
    Get a user.
    """
    database_exception = HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=[jsonable_encoder(Error(type=ErrorType.DATABASE,
            msg="unable to validate credentials",
        ))],
    )

    try:
        user = session.get(User, id)
    except Exception as e:
        raise database_exception from e

    if not user:
        return None

    return user

def get_current_user(token: TokenDep,
    security_scopes: SecurityScopes,
    session: SessionDep,
) -> User:
    """
    Get the current user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=[jsonable_encoder(Error(type=ErrorType.UNAUTHORIZED,
            msg="unable to validate credentials",
        ))],
        headers={"WWW-Authenticate": "Bearer"},
    )

    if security_scopes.scopes:
        credentials_exception.headers = {
            "WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'
        }

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(user_id=user_id, scopes=token_scopes)
    except (InvalidTokenError, ValidationError):
        raise credentials_exception

    user = get_user(id=token_data.user_id or "", session=session)
    if not user:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            credentials_exception.detail = "insufficent permissions"
            raise credentials_exception
    return user

@router.get("/", tags=["user"])
def get_current_active_user(
    current_user: Annotated[User,
        Security(get_current_user, scopes=["user:read"])],
) -> UserData:
    """
    Get the current user, if active.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=[jsonable_encoder(Error(type=ErrorType.UNAUTHORIZED,
            msg="unable to validate credentials",
        ))],
        headers={"WWW-Authenticate": "Bearer"},
    )

    if current_user.status != "active":
        raise credentials_exception
    return current_user

def authenticate_user(user_id: str, password: str, session: SessionDep,
) -> User | None:
    """
    Authenticate a user by ID and password.
    """
    user = get_user(user_id, session)
    if not user:
        return None
    if not verify_password(password, user.hashed_password or ""):
        return None
    return user

def UserSecurity(scopes: list[str]) -> Annotated:
    """
    Security dependency for the current active user.
    """
    return Security(get_current_active_user, scopes=scopes)
