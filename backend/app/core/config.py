from functools import lru_cache
from pathlib import Path
from typing import Annotated, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    project_name: str = "Enterprise AI Copilot"
    environment: str = "development"
    secret_key: str = Field(..., alias="SECRET_KEY")
    cors_origins: Annotated[List[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"], alias="CORS_ORIGINS"
    )

    postgres_url: str = Field(..., alias="POSTGRES_URL")
    redis_url: str = Field(..., alias="REDIS_URL")

    upload_dir: Path = Field(default=Path("data/uploads"), alias="UPLOAD_DIR")
    vector_store_path: Path = Field(default=Path("data/vector_store"), alias="VECTOR_STORE_PATH")

    cache_ttl_seconds: int = Field(default=900, alias="CACHE_TTL_SECONDS")
    retrieval_top_k: int = Field(default=4, alias="RETRIEVAL_TOP_K")
    retrieval_candidate_multiplier: int = Field(default=3, alias="RETRIEVAL_CANDIDATE_MULTIPLIER")
    hybrid_semantic_weight: float = Field(default=0.65, alias="HYBRID_SEMANTIC_WEIGHT")
    hybrid_keyword_weight: float = Field(default=0.35, alias="HYBRID_KEYWORD_WEIGHT")
    max_upload_size_mb: int = Field(default=20, alias="MAX_UPLOAD_SIZE_MB")
    max_context_characters: int = Field(default=6000, alias="MAX_CONTEXT_CHARACTERS")
    llm_timeout_seconds: int = Field(default=45, alias="LLM_TIMEOUT_SECONDS")
    llm_max_concurrency: int = Field(default=8, alias="LLM_MAX_CONCURRENCY")
    enable_grounding_validation: bool = Field(default=True, alias="ENABLE_GROUNDING_VALIDATION")
    memory_window_size: int = Field(default=6, alias="MEMORY_WINDOW_SIZE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    default_role: str = Field(default="viewer", alias="DEFAULT_ROLE")

    azure_openai_endpoint: str = Field(..., alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field(..., alias="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field(..., alias="AZURE_OPENAI_API_VERSION")
    azure_openai_chat_deployment: str = Field(..., alias="AZURE_OPENAI_CHAT_DEPLOYMENT")
    azure_openai_fast_deployment: str = Field(..., alias="AZURE_OPENAI_FAST_DEPLOYMENT")
    azure_openai_embedding_deployment: str = Field(..., alias="AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, list):
            return value
        return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.vector_store_path.mkdir(parents=True, exist_ok=True)
    return settings
