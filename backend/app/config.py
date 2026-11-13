from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BASE_DIR.parent


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://anapec:anapec@localhost:5433/anapec"
    jwt_secret: str = "anapec-dev-secret-change-me"
    jwt_hours: int = 12
    upload_dir: str = str(BASE_DIR / "uploads")

    # Chemins des données (Standard Cookiecutter Data Science)
    data_dir: str = str(PROJECT_DIR / "data")
    raw_dir: str = str(PROJECT_DIR / "data" / "raw" / "esco")
    interim_dir: str = str(PROJECT_DIR / "data" / "interim")
    processed_dir: str = str(PROJECT_DIR / "data" / "processed")
    external_dir: str = str(PROJECT_DIR / "data" / "external")

    # Chemins modèles, rapports et références
    models_dir: str = str(PROJECT_DIR / "models")
    reports_dir: str = str(PROJECT_DIR / "reports")
    references_dir: str = str(PROJECT_DIR / "references")

    # Alias rétrocompatible pour ESCO
    esco_dir: str = str(PROJECT_DIR / "data" / "raw" / "esco")

    model_config = SettingsConfigDict(
        env_file=(str(BASE_DIR / ".env"), str(PROJECT_DIR / ".env")),
        extra="ignore",
    )


settings = Settings()
