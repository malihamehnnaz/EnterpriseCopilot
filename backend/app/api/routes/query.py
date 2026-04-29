import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_services, get_user_context
from app.schemas.chat import QueryRequest, QueryResponse
from app.services.service_registry import ServiceRegistry

router = APIRouter(tags=["query"])
logger = logging.getLogger(__name__)


@router.post("/query", response_model=QueryResponse)
async def query_copilot(
    payload: QueryRequest,
    user=Depends(get_user_context),
    services: ServiceRegistry = Depends(get_services),
) -> QueryResponse:
    if payload.session_id and not user.session_id:
        user.session_id = payload.session_id
    logger.info("query.request.received")
    cached = await services.chat_service.get_cached_response(payload.message, user.role, payload.task_type)
    if cached:
        logger.info("query.cache.hit")
        cached.session_id = user.session_id
        return cached

    response = await services.workflow.run(payload.message, payload.task_type, user.user_id, user.role, user.session_id)
    await services.chat_service.cache_response(payload.message, user.role, payload.task_type, response)
    await services.chat_service.store_memory(user.user_id, user.session_id, payload.message, response.answer)
    await services.logging_service.log_query(
        user_id=user.user_id,
        role=user.role,
        request_type="query",
        query_text=payload.message,
        response_text=response.answer,
        model_name=response.model_used,
        token_usage=response.token_usage,
        sources=response.sources,
    )
    response.session_id = user.session_id
    logger.info("query.request.completed")
    return response
