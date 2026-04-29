from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.agents.workflow import CopilotWorkflow
from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.db.session import init_db
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
from app.services.service_registry import ServiceRegistry

settings = get_settings()
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    llm_service = LLMService()
    rag_service = RAGService(llm_service)
    cache_service = CacheService()
    memory_service = MemoryService(cache_service)
    action_service = ActionService(llm_service)
    logging_service = QueryLoggingService()
    feedback_service = FeedbackService()
    evaluation_service = EvaluationService()
    document_processor = DocumentProcessor()
    chat_service = ChatService(rag_service, llm_service, cache_service, logging_service, action_service, memory_service)
    workflow = CopilotWorkflow(rag_service, llm_service, action_service, memory_service)

    await init_db()
    await cache_service.connect()
    await rag_service.initialize()

    app.state.services = ServiceRegistry(
        llm_service=llm_service,
        rag_service=rag_service,
        cache_service=cache_service,
        document_processor=document_processor,
        logging_service=logging_service,
        action_service=action_service,
        chat_service=chat_service,
        memory_service=memory_service,
        feedback_service=feedback_service,
        evaluation_service=evaluation_service,
        workflow=workflow,
    )
    yield
    await cache_service.disconnect()


app = FastAPI(title=settings.project_name, lifespan=lifespan)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    logger.warning("app.error", extra={"method": request.method, "path": request.url.path})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "detail": exc.detail,
            "request_id": getattr(request.state, "request_id", "-"),
        },
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning("request.validation_error", extra={"method": request.method, "path": request.url.path})
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "detail": "Request validation failed",
            "issues": exc.errors(),
            "request_id": getattr(request.state, "request_id", "-"),
        },
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("app.unhandled_exception", extra={"method": request.method, "path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": "An unexpected server error occurred",
            "request_id": getattr(request.state, "request_id", "-"),
        },
    )
