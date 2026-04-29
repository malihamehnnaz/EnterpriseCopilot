import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Iterable

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.core.config import get_settings
from app.core.security import is_authorized_for_roles
from app.schemas.common import SourceItem
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RetrievedChunk:
    content: str
    source: SourceItem


class RAGService:
    """Indexes enterprise documents and retrieves role-filtered context."""

    def __init__(self, llm_service: LLMService) -> None:
        self.settings = get_settings()
        self.llm_service = llm_service
        self._vector_store: FAISS | None = None
        self._lock = asyncio.Lock()

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {token for token in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(token) > 2}

    def _keyword_candidates(self, query: str, candidate_count: int) -> list[tuple[Document, float]]:
        if self._vector_store is None:
            return []
        docstore = getattr(self._vector_store.docstore, "_dict", {})
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        scored: list[tuple[Document, float]] = []
        for item in docstore.values():
            if not isinstance(item, Document):
                continue
            content_terms = self._tokenize(item.page_content)
            if not content_terms:
                continue
            overlap = len(query_terms & content_terms)
            if overlap == 0:
                continue
            scored.append((item, overlap / max(1, len(query_terms))))
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:candidate_count]

    @staticmethod
    def _combine_rankings(
        semantic_results: list[tuple[Document, float]],
        keyword_results: list[tuple[Document, float]],
        semantic_weight: float,
        keyword_weight: float,
    ) -> list[tuple[Document, float, str]]:
        fused: dict[str, tuple[Document, float, list[str]]] = {}

        semantic_max = max((score for _, score in semantic_results), default=1.0) or 1.0
        for document, distance in semantic_results:
            chunk_id = str(document.metadata.get("chunk_id", "n/a"))
            normalized = 1.0 - min(1.0, float(distance) / semantic_max)
            fused[chunk_id] = (document, semantic_weight * normalized, ["semantic"])

        keyword_max = max((score for _, score in keyword_results), default=1.0) or 1.0
        for document, score in keyword_results:
            chunk_id = str(document.metadata.get("chunk_id", "n/a"))
            normalized = float(score) / keyword_max
            if chunk_id in fused:
                existing_document, existing_score, methods = fused[chunk_id]
                methods.append("keyword")
                fused[chunk_id] = (existing_document, existing_score + keyword_weight * normalized, methods)
            else:
                fused[chunk_id] = (document, keyword_weight * normalized, ["keyword"])

        ranked = [(document, score, "+".join(sorted(set(methods)))) for document, score, methods in fused.values()]
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked

    async def initialize(self) -> None:
        index_path = self.settings.vector_store_path
        faiss_index = index_path / "index.faiss"
        if faiss_index.exists():
            self._vector_store = await asyncio.to_thread(
                FAISS.load_local,
                str(index_path),
                self.llm_service.embeddings,
                allow_dangerous_deserialization=True,
            )

    async def add_documents(self, documents: list[Document]) -> int:
        if not documents:
            return 0
        async with self._lock:
            if self._vector_store is None:
                self._vector_store = await asyncio.to_thread(
                    FAISS.from_documents,
                    documents,
                    self.llm_service.embeddings,
                )
            else:
                await asyncio.to_thread(self._vector_store.add_documents, documents)
            await asyncio.to_thread(self._vector_store.save_local, str(self.settings.vector_store_path))
        return len(documents)

    async def retrieve(self, query: str, user_role: str, top_k: int | None = None) -> list[RetrievedChunk]:
        if self._vector_store is None:
            return []
        limit = top_k or self.settings.retrieval_top_k
        candidate_count = max(limit, limit * self.settings.retrieval_candidate_multiplier)
        semantic_results = await asyncio.to_thread(self._vector_store.similarity_search_with_score, query, candidate_count)
        keyword_results = await asyncio.to_thread(self._keyword_candidates, query, candidate_count)
        results = self._combine_rankings(
            semantic_results,
            keyword_results,
            self.settings.hybrid_semantic_weight,
            self.settings.hybrid_keyword_weight,
        )
        filtered: list[RetrievedChunk] = []
        seen_chunk_ids: set[str] = set()
        for document, score, retrieval_method in results:
            chunk_id = document.metadata.get("chunk_id", "n/a")
            if chunk_id in seen_chunk_ids:
                continue
            allowed_roles = self._parse_roles(document.metadata.get("allowed_roles", ""))
            if not is_authorized_for_roles(user_role, allowed_roles):
                continue
            seen_chunk_ids.add(chunk_id)
            filtered.append(
                RetrievedChunk(
                    content=document.page_content,
                    source=SourceItem(
                        source=document.metadata.get("source", "Unknown"),
                        chunk_id=chunk_id,
                        page=document.metadata.get("page"),
                        score=float(score),
                        excerpt=document.page_content[:220],
                        retrieval_method=retrieval_method,
                    ),
                )
            )
            if len(filtered) >= limit:
                break
        logger.info("rag.retrieve.completed", extra={"path": "rag", "method": "RETRIEVE", "duration_ms": len(filtered)})
        return filtered

    def format_context(self, chunks: Iterable[RetrievedChunk]) -> str:
        parts: list[str] = []
        total_length = 0
        for item in chunks:
            page = f"page {item.source.page}" if item.source.page else "page n/a"
            block = f"[{item.source.chunk_id}] {item.source.source} ({page})\n{item.content}"
            remaining = self.settings.max_context_characters - total_length
            if remaining <= 0:
                break
            if len(block) > remaining:
                block = f"{block[:remaining].rstrip()}..."
            parts.append(block)
            total_length += len(block) + 2
        return "\n\n".join(parts)

    @staticmethod
    def _parse_roles(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]
