from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings managed via environment variables."""

    APP_NAME: str = "SynDataX"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "postgresql+psycopg://syndatax:syndatax@localhost:5432/syndatax"
    API_V1_STR: str = "/api/v1"

    # Dataset Storage & Limit Configurations
    MAX_UPLOAD_SIZE_MB: int = 50
    DATASET_STORAGE_PATH: str = "storage/datasets"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
