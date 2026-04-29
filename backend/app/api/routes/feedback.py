import logging

from fastapi import APIRouter, Depends, status

from app.api.deps import get_services, get_user_context
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.service_registry import ServiceRegistry

router = APIRouter(tags=["feedback"])
logger = logging.getLogger(__name__)


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackRequest,
    user=Depends(get_user_context),
    services: ServiceRegistry = Depends(get_services),
) -> FeedbackResponse:
    logger.info("feedback.request.received")
    response = await services.feedback_service.record_feedback(user.user_id, payload)
    logger.info("feedback.request.completed")
    return response