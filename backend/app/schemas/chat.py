from pydantic import BaseModel, Field

from app.schemas.common import SourceItem, TokenUsage


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    task_type: str = "qa"
    stream: bool = True
    session_id: str | None = None


class QueryRequest(BaseModel):
    message: str = Field(min_length=1)
    task_type: str = "qa"
    session_id: str | None = None


class QueryResponse(BaseModel):
    answer: str
    task_type: str
    sources: list[SourceItem] = Field(default_factory=list)
    validation: str | None = None
    model_used: str
    cached: bool = False
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    session_id: str | None = None
    memory_used: bool = False
