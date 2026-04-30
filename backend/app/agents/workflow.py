import time

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import CopilotNodes
from app.agents.orchestrator import OrchestratorAgent
from app.agents.state import CopilotState
from app.schemas.chat import QueryResponse
from app.schemas.common import SourceItem, TokenUsage
from app.services.action_service import ActionService
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.services.observability_service import ObservabilityService, build_query_record
from app.services.rag_service import RAGService


class CopilotWorkflow:
    """Compiles and executes the enterprise multi-agent workflow."""

    def __init__(self, rag_service: RAGService, llm_service: LLMService, action_service: ActionService, memory_service: MemoryService) -> None:
        self.nodes = CopilotNodes(rag_service, llm_service, action_service, memory_service)
        self._orchestrator = OrchestratorAgent()
        self._observability = ObservabilityService()

        graph = StateGraph(CopilotState)
        graph.add_node("orchestrator", self._orchestrate)
        graph.add_node("retriever", self.nodes.retriever)
        graph.add_node("specialist", self.nodes.specialist)
        graph.add_node("reasoner", self.nodes.reasoner)
        graph.add_node("validator", self.nodes.validator)
        graph.add_node("action", self.nodes.action)
        graph.add_edge(START, "orchestrator")
        graph.add_edge("orchestrator", "retriever")
        graph.add_edge("retriever", "specialist")
        graph.add_edge("specialist", "reasoner")
        graph.add_edge("reasoner", "validator")
        graph.add_edge("validator", "action")
        graph.add_edge("action", END)
        self.graph = graph.compile()

    async def _orchestrate(self, state: CopilotState) -> CopilotState:
        """Route the query to the appropriate specialized agent."""
        routing = self._orchestrator.route(state["message"])
        return routing

    async def run(self, message: str, task_type: str, user_id: str, user_role: str, session_id: str | None = None) -> QueryResponse:
        start_ms = time.monotonic()
        state = await self.graph.ainvoke(
            {
                "message": message,
                "task_type": task_type,
                "user_id": user_id,
                "user_role": user_role,
                "session_id": session_id,
            }
        )
        latency_ms = int((time.monotonic() - start_ms) * 1000)

        token_usage: TokenUsage = state.get("token_usage") or TokenUsage()
        sources: list[SourceItem] = state.get("sources", [])
        final_answer = state.get("final_answer") or state.get("draft_answer") or "No answer generated."
        validation = state.get("validation")
        active_agent = state.get("active_agent", "general")

        # Persist the full run record to the database
        record = build_query_record(
            user_id=user_id,
            session_id=session_id,
            role=user_role,
            request_type=task_type,
            active_agent=active_agent,
            query_text=message,
            response_text=final_answer,
            model_name=state.get("model_used", "unknown"),
            token_usage=token_usage,
            sources=sources,
            latency_ms=latency_ms,
            validation_result=validation,
        )
        await self._observability.log_query_run(record)

        return QueryResponse(
            answer=final_answer,
            task_type=task_type,
            sources=sources,
            validation=validation,
            model_used=state.get("model_used", "unknown"),
            token_usage=token_usage,
            session_id=session_id,
            memory_used=bool(state.get("conversation_history")),
        )
