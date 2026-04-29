import asyncio
import logging

import orjson
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_services, get_user_context
from app.schemas.chat import ChatRequest
from app.services.service_registry import ServiceRegistry

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)


def sse_event(payload: dict) -> str:
    return f"data: {orjson.dumps(payload).decode('utf-8')}\n\n"


@router.post("/chat")
async def chat_stream(
    payload: ChatRequest,
    user=Depends(get_user_context),
    services: ServiceRegistry = Depends(get_services),
) -> StreamingResponse:
    if payload.session_id and not user.session_id:
        user.session_id = payload.session_id
    logger.info("chat.request.received")
    cached = await services.chat_service.get_cached_response(payload.message, user.role, payload.task_type)
    if cached:
        logger.info("chat.cache.hit")
        cached.session_id = user.session_id
        async def cached_stream():
            yield sse_event({"type": "chunk", "content": cached.answer})
            yield sse_event({"type": "sources", "content": [item.model_dump() for item in cached.sources]})
            yield sse_event({"type": "meta", "content": {"model": cached.model_used, "cached": True, "session_id": cached.session_id}})
            yield sse_event({"type": "done"})

        return StreamingResponse(cached_stream(), media_type="text/event-stream")

    async def event_generator():
        stream, sources, context, model_name = await services.chat_service.stream_answer(payload.message, user, payload.task_type)
        chunks: list[str] = []
        async for chunk in stream:
            chunks.append(chunk)
            yield sse_event({"type": "chunk", "content": chunk})
            await asyncio.sleep(0)

        answer = "".join(chunks)
        token_usage = services.llm_service.token_service.build_usage(context + payload.message, answer)
        response = {
            "answer": answer,
            "task_type": payload.task_type,
            "sources": [item.model_dump() for item in sources],
            "validation": "streamed response",
            "model_used": model_name,
            "cached": False,
            "token_usage": token_usage.model_dump(),
        }
        await services.cache_service.set_json(
            services.chat_service.build_cache_key(payload.message, user.role, payload.task_type),
            response,
        )
        await services.logging_service.log_query(
            user_id=user.user_id,
            role=user.role,
            request_type="chat",
            query_text=payload.message,
            response_text=answer,
            model_name=model_name,
            token_usage=token_usage,
            sources=sources,
        )
        await services.chat_service.store_memory(user.user_id, user.session_id, payload.message, answer)
        logger.info("chat.request.completed")
        yield sse_event({"type": "sources", "content": response["sources"]})
        yield sse_event({"type": "meta", "content": {"model": model_name, "cached": False, "session_id": user.session_id}})
        yield sse_event({"type": "done"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")
