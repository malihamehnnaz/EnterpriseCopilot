from typing import Any

from pydantic import BaseModel, Field


class SourceItem(BaseModel):
    source: str
    chunk_id: str
    page: int | None = None
    score: float | None = None
    excerpt: str | None = None
    retrieval_method: str | None = None


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ApiMessage(BaseModel):
    message: str
    meta: dict[str, Any] = Field(default_factory=dict)


class RetrievalMetrics(BaseModel):
    precision_at_k: float = 0.0
    recall_at_k: float = 0.0
    matched_chunk_ids: list[str] = Field(default_factory=list)
