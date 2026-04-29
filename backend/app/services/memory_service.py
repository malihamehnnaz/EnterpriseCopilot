from app.core.config import get_settings
from app.services.cache_service import CacheService


class MemoryService:
    """Stores and retrieves short-term agent memory by user session."""

    def __init__(self, cache_service: CacheService) -> None:
        self.settings = get_settings()
        self.cache_service = cache_service

    def _key(self, user_id: str, session_id: str | None) -> str:
        normalized_session = session_id or "default"
        return f"memory:{user_id}:{normalized_session}"

    async def get_history(self, user_id: str, session_id: str | None) -> list[dict[str, str]]:
        payload = await self.cache_service.get_json(self._key(user_id, session_id))
        if not payload:
            return []
        history = payload.get("items", [])
        if isinstance(history, list):
            return [item for item in history if isinstance(item, dict)]
        return []

    async def append_turn(self, user_id: str, session_id: str | None, user_message: str, assistant_message: str) -> None:
        history = await self.get_history(user_id, session_id)
        history.extend(
            [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_message},
            ]
        )
        window = history[-self.settings.memory_window_size :]
        await self.cache_service.set_json(self._key(user_id, session_id), {"items": window})

    def format_history(self, history: list[dict[str, str]]) -> str:
        lines: list[str] = []
        for item in history:
            role = item.get("role", "user").capitalize()
            content = item.get("content", "").strip()
            if content:
                lines.append(f"{role}: {content}")
        return "\n".join(lines)