# api-gateway/app/config.py

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    ALGORITHM: str = "HS256"
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    TEMPLATE_SERVICE_URL: str = "http://template-service:8002"
    RENDER_SERVICE_URL: str = "http://render-service:8003"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()