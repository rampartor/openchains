from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "OpenChains"
    DEBUG: bool = False

    # Database settings
    DATABASE_URL: str = "postgres://postgres:postgres@localhost:5432/openchains"

    # Security settings
    SECRET_KEY: str = "your-default-secret-key-for-development"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Default admin user
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "changeme"

    # CORS settings
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://frontend:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create settings instance
settings = Settings()
