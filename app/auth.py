"""
Authentication types and helpers.
"""
import jwt, bcrypt
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from .config import settings

class Token(BaseModel):
    """
    An authentication token.
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Authentication token data.
    """
    user_id: str | None = None
    scopes: list[str] = []

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=settings.API_PREFIX + "/login/token",
    scopes={
        "user:read": "Read the current user.",
        "user:write": "Wrtie to the current user.",
        "resources:read": "Read resources.",
        "resources:write": "Write to resources.",
        "resources:admin": "Administer resources.",
    },
)

TokenDep = Annotated[str, Depends(oauth2_scheme)]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password matches the hashed version.
    """
    password_bytes = plain_password.encode()
    hashed_bytes = bytes.fromhex(hashed_password)
    return bcrypt.checkpw(password = password_bytes,
        hashed_password = hashed_bytes)

def get_password_hash(password) -> str:
    """
    Return the hashed version of a password.
    """
    return bcrypt.hashpw(password=password.encode(),
        salt=bcrypt.gensalt()).hex()

def create_access_token(data: dict | None = None,
    expires_delta: timedelta | None = None):
    """
    Create a JWT for API access.
    """
    if data:
        to_encode = data.copy()
    else:
        to_encode = {}

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.ACCESS_TOKEN_SECRET_KEY,
        algorithm=settings.ACCESS_TOKEN_ALGORITHM)
