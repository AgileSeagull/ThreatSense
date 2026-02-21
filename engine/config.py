from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/threat_detection"
    threat_db_path: str = "data/threat_hashes.txt"
    alert_threshold: float = 50.0
    log_level: str = "INFO"
    api_key: str | None = None  # If set, require Authorization: Bearer <api_key> for /api/v1

    class Config:
        env_prefix = "ENGINE_"
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
