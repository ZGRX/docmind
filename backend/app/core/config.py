from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    chat_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    database_url: str = "sqlite:///./data/app.db"
    chroma_path: str = "./data/chroma"
    upload_dir: str = "./data/uploads"
    cors_origins: str = "http://localhost:5173"
    max_upload_mb: int = 15
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 5

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
