import logging

from app.db.models import QueryLog
from app.db.session import SessionLocal
from app.schemas.common import SourceItem, TokenUsage

logger = logging.getLogger(__name__)


class QueryLoggingService:
    """Persists auditable chat and query activity."""

    async def log_query(
        self,
        user_id: str,
        role: str,
        request_type: str,
        query_text: str,
        response_text: str,
        model_name: str,
        token_usage: TokenUsage,
        sources: list[SourceItem],
        *,
        session_id: str | None = None,
        active_agent: str = "general",
        latency_ms: int = 0,
        validation_result: str | None = None,
    ) -> None:
        try:
            async with SessionLocal() as session:
                session.add(
                    QueryLog(
                        user_id=user_id,
                        session_id=session_id,
                        role=role,
                        request_type=request_type,
                        active_agent=active_agent,
                        query_text=query_text,
                        response_text=response_text,
                        model_name=model_name,
                        prompt_tokens=token_usage.prompt_tokens,
                        completion_tokens=token_usage.completion_tokens,
                        total_tokens=token_usage.total_tokens,
                        latency_ms=latency_ms,
                        validation_result=validation_result,
                        source_payload={"sources": [source.model_dump() for source in sources]},
                    )
                )
                await session.commit()
        except Exception as exc:  # pragma: no cover - runtime resiliency
            logger.warning("Failed to persist query log: %s", exc)
