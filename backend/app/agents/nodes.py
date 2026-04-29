from app.agents.state import CopilotState
from app.schemas.common import TokenUsage
from app.services.action_service import ActionService
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.services.rag_service import RAGService


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
        prompt = (
            f"Role: {state['user_role']}\n"
            f"Task: {state['task_type']}\n"
            f"Conversation memory:\n{state.get('conversation_history') or 'No prior memory available.'}\n\n"
            f"Question: {state['message']}\n\n"
            f"Approved context:\n{state.get('retrieved_context') or 'No approved context available.'}\n\n"
            "Instructions: Answer only using approved context. Cite chunk IDs in square brackets. "
            "If there is not enough information, say that explicitly."
        )
        answer = await self.llm_service.complete(
            "You are a secure enterprise reasoning agent.",
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
