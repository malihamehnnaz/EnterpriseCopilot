from app.services.llm_service import LLMService


class ActionService:
    """Transforms grounded answers into enterprise actions."""

    def __init__(self, llm_service: LLMService) -> None:
        self.llm_service = llm_service

    @staticmethod
    def requires_action(task_type: str) -> bool:
        return task_type.lower() in {"email", "report", "summarize"}

    async def execute(self, task_type: str, question: str, draft_answer: str, context: str) -> str:
        task = task_type.lower()
        if not self.requires_action(task):
            return draft_answer
        if not context.strip():
            return draft_answer
        if task == "email":
            return await self.llm_service.complete(
                "You generate concise professional enterprise emails.",
                f"User request: {question}\n\nGrounded content:\n{draft_answer}\n\nContext:\n{context}",
                complexity="simple",
            )
        if task == "report":
            return await self.llm_service.complete(
                "You create executive-ready enterprise reports with headings and bullets.",
                f"User request: {question}\n\nGrounded content:\n{draft_answer}\n\nContext:\n{context}",
                complexity="complex",
            )
        if task == "summarize":
            return await self.llm_service.complete(
                "You create faithful summaries using only grounded source content.",
                f"User request: {question}\n\nGrounded content:\n{draft_answer}\n\nContext:\n{context}",
                complexity="simple",
            )
        return draft_answer
