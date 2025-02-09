"""
API routing for users.
"""
import json, jwt
from jwt.exceptions import InvalidTokenError
from typing import Annotated, Any
from pydantic import ValidationError
from fastapi import APIRouter, HTTPException, Security, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import SecurityScopes
from ..errors import Error, ErrorType
from ..db import SessionDep
from ..auth import TokenDep, TokenData, verify_password
from ..config import settings
from ..models import User, UserData, UserUpdate

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
        payload = jwt.decode(token, settings.ACCESS_TOKEN_SECRET_KEY,
            algorithms=[settings.ACCESS_TOKEN_ALGORITHM])
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
    if "superuser" not in (user.scopes or []):
        for scope in security_scopes.scopes:
            if scope not in token_data.scopes:
                credentials_exception.detail = "insufficent permissions"
                raise credentials_exception
    return user

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

@router.get("/", tags=["user"],
    summary = "Get current user")
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

def UserSecurity(scopes: list[str]) -> Any:
    """
    Security dependency for the current active user.
    """
    return Security(get_current_active_user, scopes=scopes)

@router.patch("/", tags=["user"],
    summary="Update current user")
def update_user(
    user: UserUpdate,
    current_user: Annotated[User, UserSecurity(scopes=["user:write"])],
    session: SessionDep,
) -> UserData:
    """
    Update the current user.
    """
    try:
        current = session.get(User, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[jsonable_encoder(Error(type=ErrorType.DATABASE,
                msg="unable to get current user",
                input={
                    "id": current_user.id,
                    "user": user.model_dump(warnings="none"),
                },
                ctx={"error":str(e)},
            ))]) from e
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
            detail=[jsonable_encoder(Error(type=ErrorType.NOT_FOUND,
                msg="resource not found",
                input={
                    "id": current_user.id,
                    "user": user.model_dump(warnings="none"),
                },
            ))])
    current.sqlmodel_update(user.model_dump(exclude_unset=True))
    try:
        current.model_validate(current)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[jsonable_encoder(Error(type=ErrorType.INVALID_REQUEST,
                msg="invalid user",
                input={"id":id, "user":user.model_dump(warnings="none")},
                ctx=json.loads(e.json()),
            ))])
    try:
        session.add(current)
        session.commit()
        session.refresh(current)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[jsonable_encoder(Error(type=ErrorType.DATABASE,
                msg="unable to update user",
                input={
                    "id":current.id,
                    "user":current.model_dump(warnings="none"),
                },
                ctx={"error":str(e)},
            ))]) from e
    return current
