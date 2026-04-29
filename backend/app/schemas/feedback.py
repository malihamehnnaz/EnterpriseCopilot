import uuid

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    query_log_id: uuid.UUID | None = None
    session_id: str | None = None
    helpful: bool
    rating: int = Field(ge=1, le=5)
    feedback_text: str | None = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    feedback_id: str
    status: str = "recorded"