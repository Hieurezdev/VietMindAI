from functools import lru_cache
import os
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    env: str = os.getenv("ENV", "dev")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # LLM / Embeddings
    openai_api_key: str | None = None
    gemini_api_key: str = os.getenv("GEMINI_API_KEY")
    openai_model: str = "gpt-4o-mini"
    gemini_model: str = "gemini-2.5-flash"
    rag_model: str = "gemini-2.5-flash"
    
    # DB
    database_url: str | None = None  # e.g., postgres+psycopg://user:pass@host/db

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
