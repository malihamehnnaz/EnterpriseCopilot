from typing import TypedDict

from app.schemas.common import SourceItem, TokenUsage


class CopilotState(TypedDict, total=False):
    message: str
    task_type: str
    user_id: str
    user_role: str
    session_id: str | None
    # Orchestrator routing
    active_agent: str
    agent_description: str
    # Retrieval
    conversation_history: str
    retrieved_context: str
    sources: list[SourceItem]
    # Generation
    draft_answer: str
    final_answer: str
    validation: str
    model_used: str
    token_usage: TokenUsage
