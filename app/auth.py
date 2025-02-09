"""
Authentication types and helpers.
"""
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from .config import settings

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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
        "resources:write": "Write resources.",
        "resources:admin": "Administer resources.",
    },
)

TokenDep = Annotated[str, Depends(oauth2_scheme)]

def verify_password(plain_password: str | bytes,
    hashed_password: str | bytes) -> bool:
    """
    Verify a password matches the hashed version.
    """
    if isinstance(plain_password, str):
        password_bytes = plain_password.encode('utf-8')
    else:
        password_bytes = plain_password

    if isinstance(hashed_password, str):
        hashed_bytes = hashed_password.encode('utf-8')
    else:
        hashed_bytes = hashed_password

    return bcrypt.checkpw(password = password_bytes ,
        hashed_password = hashed_bytes)

def get_password_hash(password) -> str:
    """
    Return the hashed version of a password.
    """
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return str(hashed_password)

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

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
