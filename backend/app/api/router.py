from fastapi import APIRouter

from app.api.routes.chat import router as chat_router
from app.api.routes.evaluation import router as evaluation_router
from app.api.routes.feedback import router as feedback_router
from app.api.routes.health import router as health_router
from app.api.routes.query import router as query_router
from app.api.routes.upload import router as upload_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(upload_router)
api_router.include_router(chat_router)
api_router.include_router(query_router)
api_router.include_router(feedback_router)
api_router.include_router(evaluation_router)
