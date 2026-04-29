from dataclasses import dataclass

from app.agents.workflow import CopilotWorkflow
from app.services.action_service import ActionService
from app.services.cache_service import CacheService
from app.services.chat_service import ChatService
from app.services.document_processor import DocumentProcessor
from app.services.evaluation_service import EvaluationService
from app.services.feedback_service import FeedbackService
from app.services.llm_service import LLMService
from app.services.logging_service import QueryLoggingService
from app.services.memory_service import MemoryService
from app.services.rag_service import RAGService


@dataclass(slots=True)
class ServiceRegistry:
    llm_service: LLMService
    rag_service: RAGService
    cache_service: CacheService
    document_processor: DocumentProcessor
    logging_service: QueryLoggingService
    action_service: ActionService
    chat_service: ChatService
    memory_service: MemoryService
    feedback_service: FeedbackService
    evaluation_service: EvaluationService
    workflow: CopilotWorkflow
