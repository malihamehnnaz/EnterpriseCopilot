from app.agents.analytics_agent import AnalyticsAgent
from app.agents.compliance_agent import ComplianceAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.hr_agent import HRAgent
from app.agents.report_agent import ReportGenerationAgent
from app.agents.state import CopilotState
from app.agents.workflow_agent import WorkflowAgent
from app.schemas.common import TokenUsage
from app.services.action_service import ActionService
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.services.rag_service import RAGService

# Specialist agent registry — maps active_agent name → agent instance
_SPECIALIST_AGENTS = {
    "hr": HRAgent(),
    "finance": FinanceAgent(),
    "compliance": ComplianceAgent(),
    "analytics": AnalyticsAgent(),
    "report": ReportGenerationAgent(),
    "workflow": WorkflowAgent(),
}


class CopilotNodes:
    """LangGraph nodes for retrieval, reasoning, validation, and actions."""

    def __init__(self, rag_service: RAGService, llm_service: LLMService, action_service: ActionService, memory_service: MemoryService) -> None:
        self.rag_service = rag_service
        self.llm_service = llm_service
        self.action_service = action_service
        self.memory_service = memory_service

    async def retriever(self, state: CopilotState) -> CopilotState:
        chunks = await self.rag_service.retrieve(state["message"], state["user_role"])
        history = await self.memory_service.get_history(state["user_id"], state.get("session_id"))
        return {
            "conversation_history": self.memory_service.format_history(history),
            "retrieved_context": self.rag_service.format_context(chunks),
            "sources": [chunk.source for chunk in chunks],
        }

    async def specialist(self, state: CopilotState) -> CopilotState:
        """
        Dispatch to the active specialized agent to build a domain-specific prompt.
        Falls back to a generic prompt if no specialist is matched.
        """
        agent_key = state.get("active_agent", "general")
        context = state.get("retrieved_context", "")
        query = state["message"]
        user_role = state.get("user_role", "employee")

        agent = _SPECIALIST_AGENTS.get(agent_key)
        if agent and hasattr(agent, "build_prompt"):
            specialist_prompt = agent.build_prompt(query, context, user_role)
        else:
            specialist_prompt = (
                f"You are a knowledgeable enterprise assistant.\n"
                f"User Role: {user_role}\n"
                f"Question: {query}\n\n"
                f"Context:\n{context or 'No context available.'}\n\n"
                "Answer clearly and cite your sources:"
            )
        return {"specialist_prompt": specialist_prompt}

    async def reasoner(self, state: CopilotState) -> CopilotState:
        if not (state.get("retrieved_context") or "").strip():
            answer = (
                "I could not find approved source material for this request. "
                "Please upload a relevant document or verify your access role before retrying."
            )
            return {
                "draft_answer": answer,
                "model_used": "none",
                "token_usage": self.llm_service.token_service.build_usage(state["message"], answer),
            }
        complexity = self.llm_service.classify_complexity(state["message"])

        # Use the specialist-built prompt if available, otherwise fall back to the generic prompt
        specialist_prompt = state.get("specialist_prompt", "").strip()
        if specialist_prompt:
            prompt = (
                f"{specialist_prompt}\n\n"
                f"Conversation memory:\n{state.get('conversation_history') or 'No prior memory available.'}\n\n"
                "Instructions: Answer only using approved context above. Cite chunk IDs in square brackets. "
                "If there is not enough information, say that explicitly."
            )
            system_msg = f"You are a secure enterprise {state.get('active_agent', 'general')} agent."
        else:
            prompt = (
                f"Role: {state['user_role']}\n"
                f"Task: {state['task_type']}\n"
                f"Conversation memory:\n{state.get('conversation_history') or 'No prior memory available.'}\n\n"
                f"Question: {state['message']}\n\n"
                f"Approved context:\n{state.get('retrieved_context') or 'No approved context available.'}\n\n"
                "Instructions: Answer only using approved context. Cite chunk IDs in square brackets. "
                "If there is not enough information, say that explicitly."
            )
            system_msg = "You are a secure enterprise reasoning agent."

        answer = await self.llm_service.complete(
            system_msg,
            prompt,
            complexity=complexity,
        )
        return {
            "draft_answer": answer,
            "model_used": self.llm_service.get_model_name(complexity),
            "token_usage": self.llm_service.token_service.build_usage(prompt, answer),
        }

    async def validator(self, state: CopilotState) -> CopilotState:
        if state.get("model_used") == "none":
            return {"validation": "skipped: no approved context"}
        if state.get("task_type", "qa").lower() == "qa" and self.llm_service.classify_complexity(state["message"]) == "simple":
            return {"validation": "skipped: simple qa"}
        result = await self.llm_service.validate_grounding(
            state["message"],
            state.get("draft_answer", ""),
            state.get("retrieved_context", ""),
        )
        first_line = result.splitlines()[0].strip().upper() if result else "FAIL"
        validation = "passed" if first_line.startswith("PASS") else "failed"
        return {"validation": f"{validation}: {result}"}

    async def action(self, state: CopilotState) -> CopilotState:
        if not self.action_service.requires_action(state["task_type"]):
            return {
                "final_answer": state.get("draft_answer", ""),
                "token_usage": state.get("token_usage") or TokenUsage(),
            }
        final_answer = await self.action_service.execute(
            state["task_type"],
            state["message"],
            state.get("draft_answer", ""),
            state.get("retrieved_context", ""),
        )
        token_usage = state.get("token_usage") or TokenUsage()
        if final_answer != state.get("draft_answer", ""):
            token_usage = self.llm_service.token_service.build_usage(
                state.get("draft_answer", ""),
                final_answer,
            )
        return {
            "final_answer": final_answer,
            "token_usage": token_usage,
        }
