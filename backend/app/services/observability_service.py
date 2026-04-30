import logging
import uuid
from datetime import datetime, timezone

from app.db.models import AgentExecutionLog, NotificationRecord, QueryLog, WorkflowRecord
from app.db.session import SessionLocal
from app.schemas.common import SourceItem, TokenUsage

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Pure data-building helpers (testable without a DB connection)
# ---------------------------------------------------------------------------

def build_query_record(
    *,
    user_id: str,
    session_id: str | None,
    role: str,
    request_type: str,
    active_agent: str,
    query_text: str,
    response_text: str,
    model_name: str,
    token_usage: TokenUsage,
    sources: list[SourceItem],
    latency_ms: int,
    validation_result: str | None,
) -> dict:
    """
    Build a plain dict representing a QueryLog row.
    No DB connection required — useful for testing and inspection.
    """
    return {
        "user_id": user_id,
        "session_id": session_id,
        "role": role,
        "request_type": request_type,
        "active_agent": active_agent,
        "query_text": query_text,
        "response_text": response_text,
        "model_name": model_name,
        "prompt_tokens": token_usage.prompt_tokens,
        "completion_tokens": token_usage.completion_tokens,
        "total_tokens": token_usage.total_tokens,
        "latency_ms": latency_ms,
        "validation_result": validation_result,
        "source_payload": {"sources": [s.model_dump() for s in sources]},
    }


def build_agent_execution_record(
    *,
    agent_name: str,
    user_id: str,
    input_text: str,
    output_text: str,
    latency_ms: int,
    token_count: int = 0,
    success: bool = True,
    error_message: str | None = None,
    query_log_id: uuid.UUID | None = None,
) -> dict:
    """Build a plain dict representing an AgentExecutionLog row."""
    return {
        "agent_name": agent_name,
        "user_id": user_id,
        "query_log_id": query_log_id,
        "input_preview": input_text[:500],
        "output_preview": output_text[:500],
        "latency_ms": latency_ms,
        "token_count": token_count,
        "success": success,
        "error_message": error_message,
    }


def build_workflow_record(
    *,
    user_id: str,
    goal: str,
    tasks: list[dict],
    requires_approval: bool,
    query_log_id: uuid.UUID | None = None,
) -> dict:
    """Build a plain dict representing a WorkflowRecord row."""
    return {
        "user_id": user_id,
        "query_log_id": query_log_id,
        "goal": goal,
        "tasks_json": {"tasks": tasks},
        "requires_approval": requires_approval,
        "approval_status": "pending" if requires_approval else "not_required",
    }


def build_notification_record(
    *,
    user_id: str,
    event_name: str,
    recipients: list[str],
    body: str,
    query_log_id: uuid.UUID | None = None,
) -> dict:
    """Build a plain dict representing a NotificationRecord row."""
    return {
        "user_id": user_id,
        "query_log_id": query_log_id,
        "event_name": event_name,
        "recipients_json": {"recipients": recipients},
        "body": body,
        "delivered": False,
    }


def compute_dashboard_stats(records: list[dict]) -> dict:
    """
    Compute aggregate observability statistics from a list of query record dicts.
    Pure function — no DB required. Suitable for dashboards and reporting.

    Each record dict should have: total_tokens, latency_ms, active_agent, model_name.
    """
    if not records:
        return {
            "total_queries": 0,
            "avg_latency_ms": 0.0,
            "avg_tokens": 0.0,
            "total_tokens": 0,
            "agent_distribution": {},
            "model_distribution": {},
            "p95_latency_ms": 0.0,
        }

    total = len(records)
    latencies = sorted(r.get("latency_ms", 0) for r in records)
    tokens = [r.get("total_tokens", 0) for r in records]

    agent_dist: dict[str, int] = {}
    model_dist: dict[str, int] = {}
    for r in records:
        agent = r.get("active_agent", "unknown")
        model = r.get("model_name", "unknown")
        agent_dist[agent] = agent_dist.get(agent, 0) + 1
        model_dist[model] = model_dist.get(model, 0) + 1

    # p95 latency
    p95_index = max(0, int(total * 0.95) - 1)
    p95_latency = latencies[p95_index]

    return {
        "total_queries": total,
        "avg_latency_ms": round(sum(latencies) / total, 2),
        "avg_tokens": round(sum(tokens) / total, 2),
        "total_tokens": sum(tokens),
        "agent_distribution": agent_dist,
        "model_distribution": model_dist,
        "p95_latency_ms": float(p95_latency),
    }


# ---------------------------------------------------------------------------
# Database write methods
# ---------------------------------------------------------------------------

class ObservabilityService:
    """
    Persists all agent execution, query, workflow, and notification records to the DB.
    Every interaction is recorded for audit, analytics, and observability.
    """

    async def log_query_run(self, record: dict) -> uuid.UUID | None:
        """Persist a full query run record. Returns the new QueryLog UUID."""
        try:
            async with SessionLocal() as session:
                log = QueryLog(**record)
                session.add(log)
                await session.commit()
                await session.refresh(log)
                return log.id
        except Exception as exc:  # pragma: no cover
            logger.warning("ObservabilityService.log_query_run failed: %s", exc)
            return None

    async def log_agent_execution(self, record: dict) -> None:
        """Persist an agent node execution record."""
        try:
            async with SessionLocal() as session:
                session.add(AgentExecutionLog(**record))
                await session.commit()
        except Exception as exc:  # pragma: no cover
            logger.warning("ObservabilityService.log_agent_execution failed: %s", exc)

    async def log_workflow(self, record: dict) -> uuid.UUID | None:
        """Persist a workflow plan record. Returns the new WorkflowRecord UUID."""
        try:
            async with SessionLocal() as session:
                wf = WorkflowRecord(**record)
                session.add(wf)
                await session.commit()
                await session.refresh(wf)
                return wf.id
        except Exception as exc:  # pragma: no cover
            logger.warning("ObservabilityService.log_workflow failed: %s", exc)
            return None

    async def log_notification(self, record: dict) -> None:
        """Persist a notification dispatch record."""
        try:
            async with SessionLocal() as session:
                session.add(NotificationRecord(**record))
                await session.commit()
        except Exception as exc:  # pragma: no cover
            logger.warning("ObservabilityService.log_notification failed: %s", exc)
