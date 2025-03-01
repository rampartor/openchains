import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgres://postgres:postgres@localhost:5432/openchains"
    )

    # Application settings
    APP_NAME: str = "OpenChains"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-development")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
