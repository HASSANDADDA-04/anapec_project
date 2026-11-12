from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BASE_DIR.parent


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://anapec:anapec@localhost:5433/anapec"
    jwt_secret: str = "anapec-dev-secret-change-me"
    jwt_hours: int = 12
    esco_dir: str = str(PROJECT_DIR / "data" / "esco" / "fr")
    upload_dir: str = str(BASE_DIR / "uploads")
    models_dir: str = str(PROJECT_DIR / "models")
    reports_dir: str = str(PROJECT_DIR / "reports")

    model_config = SettingsConfigDict(
        env_file=(str(BASE_DIR / ".env"), str(PROJECT_DIR / ".env")),
        extra="ignore",
    )


settings = Settings()
