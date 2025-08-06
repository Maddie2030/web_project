# api-gateway/app/settings.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    AUTH_SERVICE_URL: str
    TEMPLATE_SERVICE_URL: str
    RENDER_SERVICE_URL: str
    JWT_SECRET_KEY: str

    # Define public routes here for easy management
    public_routes: list[str] = [
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/health",
        "/"
    ]

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()