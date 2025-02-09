"""
Database session access.
"""
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

sqlite_file_name = "api.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_all():
    """
    Perform all database migrations.
    """
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Yeild a single database session.
    """
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
