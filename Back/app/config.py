from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "gym_admin"
    DB_PASSWORD: str
    DB_NAME: str = "gym_management"

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Admin settings
    DEFAULT_ADMIN_PASSWORD: str = "1234"

    # Application settings
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()