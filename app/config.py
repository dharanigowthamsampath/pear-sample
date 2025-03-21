import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn

class Settings(BaseSettings):
    PROJECT_NAME: str = "User Management API"
    API_V1_PREFIX: str = "/api/v1"
    
    # Database settings
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pear")
    
    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Export the DB connection string as a string
DB_CONNECTION_STRING = settings.DATABASE_URL