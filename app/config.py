"""
Configuration settings management.
"""
import secrets
from typing import Annotated, Any
from pydantic import AnyUrl, BeforeValidator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

def parse_cors(v: Any) -> list[str] | str:
    """
    Parse CORS origins from a comma separated string or list.
    """
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)

class Settings(BaseSettings):
    """
    Service configuration settings.
    """
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    API_PREFIX: str = "/api/v1"
    ACCESS_TOKEN_SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 day
    DB_URL: str = "sqlite:///api.db"
    DB_CONNECT_ARGS: Any = {"check_same_thread": False}
    SERVICE_NAME: str = "api"
    SERVICE_DESCRIPTION: str = "An application programming interface service."
    SERVICE_VERSION: str = "v0.1.1"
    SUPERUSER: str = "admin"
    SUPERUSER_PASSWORD: str = "admin"
    FRONTEND_HOST: str = "http://localhost:5173"
    CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = "http://localhost:8000"

    @computed_field
    @property
    def all_cors_origins(self) -> list[str]:
        return [
            str(origin).rstrip("/") for origin in self.CORS_ORIGINS
        ] + [
            self.FRONTEND_HOST
        ]

settings = Settings()
