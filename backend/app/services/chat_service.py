import hashlib
import logging
from typing import AsyncIterator

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.core.security import UserContext
from app.schemas.common import SourceItem
from app.schemas.chat import QueryResponse
from app.services.action_service import ActionService
from app.services.cache_service import CacheService
from app.services.llm_service import LLMService
from app.services.logging_service import QueryLoggingService
from app.services.memory_service import MemoryService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class ChatService:
    """Provides low-latency streaming chat and cached grounded answers."""

    def __init__(
        self,
        rag_service: RAGService,
        llm_service: LLMService,
        cache_service: CacheService,
        logging_service: QueryLoggingService,
        action_service: ActionService,
        memory_service: MemoryService,
    ) -> None:
        self.settings = get_settings()
        self.rag_service = rag_service
        self.llm_service = llm_service
        self.cache_service = cache_service
        self.logging_service = logging_service
        self.action_service = action_service
        self.memory_service = memory_service

    def build_cache_key(self, message: str, role: str, task_type: str) -> str:
        raw_key = f"{role}:{task_type}:{message.strip().lower()}"
        return f"chat:{hashlib.sha256(raw_key.encode()).hexdigest()}"

    def build_retrieval_cache_key(self, message: str, role: str) -> str:
        raw_key = f"retrieval:{role}:{message.strip().lower()}"
        return f"rag:{hashlib.sha256(raw_key.encode()).hexdigest()}"

    @staticmethod
    def build_no_context_response(task_type: str) -> str:
        return (
            "I could not find approved source material for this request. "
            "Please upload a relevant document or verify your access role before retrying."
        )

    async def get_cached_response(self, message: str, role: str, task_type: str) -> QueryResponse | None:
        payload = await self.cache_service.get_json(self.build_cache_key(message, role, task_type))
        if not payload:
            return None
        payload["cached"] = True
        return QueryResponse(**payload)

    async def cache_response(self, message: str, role: str, task_type: str, response: QueryResponse) -> None:
        await self.cache_service.set_json(
            self.build_cache_key(message, role, task_type),
            response.model_dump(mode="json"),
        )

    async def build_prompt(self, message: str, user: UserContext, task_type: str) -> tuple[list[SystemMessage | HumanMessage], list[SourceItem], str, str, bool]:
        history = await self.memory_service.get_history(user.user_id, user.session_id)
        formatted_history = self.memory_service.format_history(history)
        retrieval_cache_key = self.build_retrieval_cache_key(message, user.role)
        cached_retrieval = await self.cache_service.get_json(retrieval_cache_key)
        if cached_retrieval:
            context = str(cached_retrieval.get("context", ""))
            source_items = [SourceItem(**item) for item in cached_retrieval.get("sources", [])]
            logger.info("chat.retrieval_cache.hit")
        else:
            retrieved = await self.rag_service.retrieve(message, user.role)
            context = self.rag_service.format_context(retrieved)
            source_items = [item.source for item in retrieved]
            await self.cache_service.set_json(
                retrieval_cache_key,
                {
                    "context": context,
                    "sources": [item.model_dump(mode="json") for item in source_items],
                },
                ttl_seconds=max(60, self.settings.cache_ttl_seconds // 3),
            )

        complexity = self.llm_service.classify_complexity(f"{task_type} {message}")
        system_prompt = (
            "You are an enterprise copilot for internal employees. "
            "Use only the provided context. If the answer is unavailable, say so clearly. "
            "Always cite supporting chunk IDs in square brackets."
        )
        user_prompt = (
            f"Role: {user.role}\nTask type: {task_type}\nQuestion: {message}\n\n"
            f"Conversation memory:\n{formatted_history or 'No prior memory available.'}\n\n"
            f"Context:\n{context or 'No approved context available.'}"
        )
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        return messages, source_items, context, complexity, bool(formatted_history)

    async def generate_response(self, message: str, user: UserContext, task_type: str) -> QueryResponse:
        messages, sources, context, complexity, memory_used = await self.build_prompt(message, user, task_type)
        if not context.strip():
            answer = self.build_no_context_response(task_type)
            return QueryResponse(
                answer=answer,
                task_type=task_type,
                sources=sources,
                validation="skipped: no approved context",
                model_used="none",
                cached=False,
                token_usage=self.llm_service.token_service.build_usage(message, answer),
                session_id=user.session_id,
                memory_used=memory_used,
            )

        answer = await self.llm_service.complete_messages(messages, complexity)
        validation = "skipped: low-cost chat path"
        return QueryResponse(
            answer=answer,
            task_type=task_type,
            sources=sources,
            validation=validation,
            model_used=self.llm_service.get_model_name(complexity),
            cached=False,
            token_usage=self.llm_service.token_service.build_usage(context + message, answer),
            session_id=user.session_id,
            memory_used=memory_used,
        )

    async def stream_answer(self, message: str, user: UserContext, task_type: str) -> tuple[AsyncIterator[str], list[SourceItem], str, str]:
        messages, sources, context, complexity, _ = await self.build_prompt(message, user, task_type)
        if not context.strip():
            async def empty_context_stream() -> AsyncIterator[str]:
                yield self.build_no_context_response(task_type)

            return empty_context_stream(), sources, context, "none"
        return self.llm_service.stream(messages, complexity), sources, context, self.llm_service.get_model_name(complexity)

    async def store_memory(self, user_id: str, session_id: str | None, user_message: str, assistant_message: str) -> None:
        await self.memory_service.append_turn(user_id, session_id, user_message, assistant_message)
