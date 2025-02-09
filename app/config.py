"""
Configuration settings management.
"""
import secrets, warnings
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

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
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["dev", "staging", "prod"] = "dev"
    CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = "http://localhost:8000"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [
            str(origin).rstrip("/") for origin in self.CORS_ORIGINS
        ] + [
            self.FRONTEND_HOST
        ]

    SERVICE_NAME: str = "api"
    SERVICE_DESCRIPTION: str = "An application programming interface service."
    SERVICE_VERSION: str = "v0.1.1"
    SENTRY_DSN: HttpUrl | None = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "posrgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "api-db"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn(MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        ))

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.SERVICE_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)


    EMAIL_TEST_USER: str = "test@example.com"

    SUPERUSER: str = "admin"
    SUPERUSER_PASSWORD: str = "admin"

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "dev":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("ACCESS_TOKEN_SECRET_KEY",
            self.ACCESS_TOKEN_SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD",
            self.POSTGRES_PASSWORD)
        self._check_default_secret("SUPERUSER_PASSWORD",
            self.SUPERUSER_PASSWORD)

        return self

settings = Settings()
