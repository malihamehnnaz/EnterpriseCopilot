import uuid

from app.db.models import FeedbackRecord
from app.db.session import SessionLocal
from app.schemas.feedback import FeedbackRequest, FeedbackResponse


class FeedbackService:
    """Persists explicit user feedback for continuous improvement loops."""

    async def record_feedback(self, user_id: str, payload: FeedbackRequest) -> FeedbackResponse:
        feedback_id = uuid.uuid4()
        async with SessionLocal() as session:
            session.add(
                FeedbackRecord(
                    id=feedback_id,
                    query_log_id=payload.query_log_id,
                    user_id=user_id,
                    session_id=payload.session_id,
                    helpful=payload.helpful,
                    rating=payload.rating,
                    feedback_text=payload.feedback_text,
                )
            )
            await session.commit()
        return FeedbackResponse(feedback_id=str(feedback_id))