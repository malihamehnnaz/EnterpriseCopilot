import logging
import asyncio
from typing import AsyncIterator

from langchain_core.messages import AIMessageChunk, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

from app.core.config import get_settings
from app.core.exceptions import ResourceLimitError, UpstreamServiceError
from app.services.token_service import TokenService

logger = logging.getLogger(__name__)


class LLMService:
    """Handles model routing, embeddings, generation, and streaming."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.token_service = TokenService()
        self._semaphore = asyncio.Semaphore(self.settings.llm_max_concurrency)
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=self.settings.azure_openai_api_key,
            api_version=self.settings.azure_openai_api_version,
            azure_deployment=self.settings.azure_openai_embedding_deployment,
        )
        self._full_model = AzureChatOpenAI(
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=self.settings.azure_openai_api_key,
            api_version=self.settings.azure_openai_api_version,
            azure_deployment=self.settings.azure_openai_chat_deployment,
            temperature=0.2,
            max_retries=2,
            timeout=self.settings.llm_timeout_seconds,
        )
        self._fast_model = AzureChatOpenAI(
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=self.settings.azure_openai_api_key,
            api_version=self.settings.azure_openai_api_version,
            azure_deployment=self.settings.azure_openai_fast_deployment,
            temperature=0.1,
            max_retries=2,
            timeout=self.settings.llm_timeout_seconds,
        )

    def classify_complexity(self, message: str) -> str:
        lower_message = message.lower()
        complex_markers = [
            "compare",
            "analyze",
            "regulation",
            "policy",
            "risk",
            "summarize",
            "report",
            "draft",
            "email",
            "why",
            "how",
        ]
        if len(message.split()) > 35 or any(marker in lower_message for marker in complex_markers):
            return "complex"
        return "simple"

    def get_model_name(self, complexity: str) -> str:
        if complexity == "simple":
            return self.settings.azure_openai_fast_deployment
        return self.settings.azure_openai_chat_deployment

    def get_model(self, complexity: str) -> AzureChatOpenAI:
        return self._fast_model if complexity == "simple" else self._full_model

    async def _invoke_with_limits(self, operation_name: str, handler):
        try:
            async with asyncio.timeout(self.settings.llm_timeout_seconds):
                async with self._semaphore:
                    return await handler()
        except TimeoutError as exc:
            logger.exception("llm.%s.timeout", operation_name)
            raise UpstreamServiceError("Azure OpenAI request timed out") from exc
        except RuntimeError as exc:
            logger.exception("llm.%s.runtime_error", operation_name)
            raise ResourceLimitError("AI workload is temporarily saturated, please retry") from exc
        except Exception as exc:
            logger.exception("llm.%s.failed", operation_name)
            raise UpstreamServiceError("Azure OpenAI request failed") from exc

    async def complete(self, system_prompt: str, user_prompt: str, complexity: str) -> str:
        model = self.get_model(complexity)
        response = await self._invoke_with_limits(
            "complete",
            lambda: model.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]),
        )
        return response.content if isinstance(response.content, str) else str(response.content)

    async def complete_messages(self, messages: list[BaseMessage], complexity: str) -> str:
        model = self.get_model(complexity)
        response = await self._invoke_with_limits("complete_messages", lambda: model.ainvoke(messages))
        return response.content if isinstance(response.content, str) else str(response.content)

    async def stream(self, messages: list[BaseMessage], complexity: str) -> AsyncIterator[str]:
        model = self.get_model(complexity)
        try:
            async with asyncio.timeout(self.settings.llm_timeout_seconds):
                async with self._semaphore:
                    async for chunk in model.astream(messages):
                        if isinstance(chunk, AIMessageChunk):
                            content = chunk.content
                            if isinstance(content, str) and content:
                                yield content
                            elif isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and item.get("text"):
                                        yield item["text"]
        except TimeoutError as exc:
            logger.exception("llm.stream.timeout")
            raise UpstreamServiceError("Azure OpenAI stream timed out") from exc
        except Exception as exc:
            logger.exception("llm.stream.failed")
            raise UpstreamServiceError("Azure OpenAI stream failed") from exc

    async def validate_grounding(self, question: str, answer: str, context: str) -> str:
        if not self.settings.enable_grounding_validation:
            return "PASS\nValidation disabled by configuration."
        system_prompt = (
            "You are a strict enterprise compliance validator. "
            "Return PASS if the answer is grounded in the provided context. "
            "Return FAIL if it includes unsupported claims. "
            "Respond with PASS or FAIL on the first line, then a one-sentence reason."
        )
        user_prompt = f"Question:\n{question}\n\nContext:\n{context}\n\nAnswer:\n{answer}"
        return await self.complete(system_prompt, user_prompt, complexity="simple")
