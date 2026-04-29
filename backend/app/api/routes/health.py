from fastapi import APIRouter, Depends

from app.api.deps import get_services
from app.core.config import get_settings
from app.services.service_registry import ServiceRegistry

router = APIRouter(tags=["health"])


@router.get("/health")
async def healthcheck(services: ServiceRegistry = Depends(get_services)) -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.project_name,
        "environment": settings.environment,
        "components": {
            "database": "configured",
            "redis_cache": "connected" if services.cache_service._client is not None else "degraded",
            "vector_store": "ready" if services.rag_service._vector_store is not None else "empty",
            "llm": "configured",
        },
    }
