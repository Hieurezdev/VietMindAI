import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    env: str = os.getenv("ENV", "dev")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # LLM / Embeddings
    # OpenAI API key, required for OpenAI models
    openai_api_key: str | None = None
    # Hugging Face API key, required for Hugging Face models
    huggingface_api_key: str | None = None
    # Google Gemini API key, required for Gemini models
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    # Models
    openai_model: str = "gpt-4o-mini"
    thinking_gemini_model: str = "gemini-2.5-pro"
    general_gemini_model: str = "gemini-2.5-flash"
    embedding_model: str = "gemini-embedding-001"

    # Default gemini model for agents (backward compatibility)
    @property
    def gemini_model(self) -> str:
        """Default Gemini model for agents (uses general model)."""
        return self.general_gemini_model

    @property
    def rag_model(self) -> str:
        """RAG model (uses general model for speed)."""
        return self.general_gemini_model

    # DB
    database_url: str | None = None  # e.g., postgresql+asyncpg://user:pass@host:5432/db

    # Memory System
    stm_consolidation_threshold: int = 15  # Number of STM before auto-consolidation
    stm_max_threshold: int = 20  # Maximum STM before forced consolidation

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
