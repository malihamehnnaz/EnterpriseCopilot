from pydantic import BaseModel, Field

from app.schemas.common import RetrievalMetrics, SourceItem


class RetrievalEvaluationRequest(BaseModel):
    query: str = Field(min_length=1)
    relevant_chunk_ids: list[str] = Field(default_factory=list)
    top_k: int = Field(default=4, ge=1, le=20)


class RetrievalEvaluationResponse(BaseModel):
    query: str
    top_k: int
    metrics: RetrievalMetrics
    retrieved_sources: list[SourceItem] = Field(default_factory=list)