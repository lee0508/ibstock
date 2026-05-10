from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "IBStock RAG"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api"

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen3:0.6b"
    ollama_embed_model: str = "nomic-embed-text"

    sqlite_path: str = "./data/db/ibstock.db"
    faiss_index_dir: str = "./faiss_index"

    youtube_channel_url: str = "https://www.youtube.com/@Grandpa_Investor_Ib/shorts"
    youtube_channel_name: str = "IBStock"
    collection_limit: int = 50

    cors_origins: list[str] = [
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:9285",
        "http://127.0.0.1:9285",
        "null",
    ]

    @property
    def sqlite_file(self) -> Path:
        return (PROJECT_ROOT / self.sqlite_path).resolve()

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on", "debug", "dev", "development"}:
                return True
            if normalized in {"0", "false", "no", "n", "off", "release", "prod", "production"}:
                return False
        return value

    @property
    def reference_dir(self) -> Path:
        return PROJECT_ROOT / "data" / "reference"

    @property
    def faiss_dir(self) -> Path:
        return (PROJECT_ROOT / self.faiss_index_dir).resolve()


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
