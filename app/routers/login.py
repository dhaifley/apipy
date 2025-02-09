"""
API routing for authentication and login.
"""
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm
from ..errors import Error, ErrorType
from ..db import SessionDep
from ..auth import Token, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from .users import authenticate_user

router = APIRouter(
    prefix="/login",
    tags=["login"],
)

@router.post("/token",
    summary="Login for access token")
def login_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> Token:
    """
    Obtain an access token by authenticating with user_id and password.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=[jsonable_encoder(Error(type=ErrorType.UNAUTHORIZED,
            msg="unable to validate credentials",
        ))],
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = authenticate_user(user_id=form_data.username,
        password=form_data.password, session=session)
    if not user:
        raise credentials_exception

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    scopes: list[str] = []
    for scope in form_data.scopes:
        if scope in (user.scopes or []) or "superuser" in (user.scopes or []):
            scopes.append(scope)

    access_token = create_access_token(
        data={"sub": user.id, "scopes": scopes},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")
