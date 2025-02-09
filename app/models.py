"""
Service data models.
"""
import uuid
from sqlmodel import Field, SQLModel, JSON

class UserUpdate(SQLModel):
    """
    A single user's update data.
    """
    name: str | None = Field(default=None, nullable=True, index=True,
        min_length=1)
    email: str | None = Field(default=None, nullable=True, index=True,
        min_length=1)
    status: str = Field(default="active")
    data: dict | None = Field(default=None, nullable=True, sa_type=JSON)

class UserData(UserUpdate):
    """
    A single user's data.
    """
    id: str = Field(primary_key=True)

class UserCreate(UserData):
    """
    A request to create a user.
    """
    password: str

class User(UserData, table=True):
    """
    A single user.
    """
    scopes: list[str] | None = Field(default=None, nullable=True, sa_type=JSON)
    hashed_password: str | None

class Resource(SQLModel, table=True):
    """
    A single resource.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, min_length=1)
    data: dict | None = Field(default=None, nullable=True, sa_type=JSON)
