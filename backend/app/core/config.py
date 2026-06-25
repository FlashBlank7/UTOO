import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str | None = None
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"
    ALLOWED_ORIGINS: str = (
        "http://localhost:5174,"
        "http://127.0.0.1:5174,"
        "http://localhost:80,"
        "http://127.0.0.1:80,"
        "https://utoo-dev-f9d3b4fteaaqb8e9.japaneast-01.azurewebsites.net"
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if os.getenv("WEBSITE_SITE_NAME"):
            return "sqlite+aiosqlite:////home/data/utoo.db"
        return "sqlite+aiosqlite:///./utoo.db"

    class Config:
        env_file = ".env"


settings = Settings()
