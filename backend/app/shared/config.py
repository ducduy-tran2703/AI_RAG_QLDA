from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_URL_SYNC: str
    
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    APP_NAME: str = "AI Van Ban"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    UPLOAD_DIR: str = "uploads"           # Dòng này mới thêm
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()