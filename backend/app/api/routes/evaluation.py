import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_services, get_user_context
from app.schemas.evaluation import RetrievalEvaluationRequest, RetrievalEvaluationResponse
from app.services.service_registry import ServiceRegistry

router = APIRouter(tags=["evaluation"])
logger = logging.getLogger(__name__)


@router.post("/evaluation/retrieval", response_model=RetrievalEvaluationResponse)
async def evaluate_retrieval(
    payload: RetrievalEvaluationRequest,
    user=Depends(get_user_context),
    services: ServiceRegistry = Depends(get_services),
) -> RetrievalEvaluationResponse:
    logger.info("evaluation.retrieval.received")
    results = await services.rag_service.retrieve(payload.query, user.role, top_k=payload.top_k)
    retrieved_sources = [item.source for item in results]
    metrics = services.evaluation_service.retrieval_metrics(
        retrieved_chunk_ids=[item.chunk_id for item in retrieved_sources],
        relevant_chunk_ids=payload.relevant_chunk_ids,
        top_k=payload.top_k,
    )
    logger.info("evaluation.retrieval.completed")
    return RetrievalEvaluationResponse(
        query=payload.query,
        top_k=payload.top_k,
        metrics=metrics,
        retrieved_sources=retrieved_sources,
    )