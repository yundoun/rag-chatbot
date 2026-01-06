"""Application settings using Pydantic Settings"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # === Application ===
    app_name: str = "RAG Chatbot"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # === OpenAI ===
    openai_api_key: str = Field(default="")
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_temperature: float = 0.1
    openai_max_tokens: int = 2000

    # === Tavily ===
    tavily_api_key: str = Field(default="")
    tavily_max_results: int = 5

    # === ChromaDB ===
    chroma_persist_dir: str = Field(default="./data/chroma_db", alias="CHROMA_PERSIST_DIR")
    chroma_collection_name: str = "documents"

    # === RAG Settings ===
    # Lowered from 0.8 to 0.5 for better recall with small document sets
    relevance_threshold: float = 0.5
    # Lowered from 2 to 1 for small document collections
    min_high_relevance_docs: int = 1
    max_retrieval_results: int = 10
    max_correction_retries: int = 2
    max_hitl_interactions: int = 2

    # === Performance ===
    cache_ttl_seconds: int = 3600
    request_timeout_seconds: int = 30
    max_concurrent_requests: int = 10

    # === API Server ===
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # === Frontend ===
    frontend_url: str = "http://localhost:5173"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
