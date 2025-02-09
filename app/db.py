"""
Database session access.
"""
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine, select
from .config import settings
from .auth import get_password_hash
from .models import User, UserCreate


engine = create_engine(url=settings.DB_URL,
    connect_args=settings.DB_CONNECT_ARGS)

def init_db():
    """
    Perform all database migrations.
    """
    SQLModel.metadata.create_all(engine)

    user_create = UserCreate(id=settings.SUPERUSER,
        password=settings.SUPERUSER_PASSWORD)
    u = User.model_validate(
        user_create, update={
            "hashed_password": get_password_hash(user_create.password),
            "scopes": ["superuser"]
        }
    )

    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.id == settings.SUPERUSER)
        ).first()
        if not user:
            session.add(u)
            session.commit()
            session.refresh(u)

def get_session():
    """
    Yeild a single database session.
    """
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
