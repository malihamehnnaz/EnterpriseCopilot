from fastapi import Header, HTTPException, Request, status

from app.core.config import get_settings
from app.core.security import UserContext, normalize_role
from app.services.service_registry import ServiceRegistry


def get_user_context(
    x_user_id: str | None = Header(default="enterprise.user", alias="x-user-id"),
    x_user_role: str | None = Header(default=None, alias="x-user-role"),
    x_session_id: str | None = Header(default=None, alias="x-session-id"),
) -> UserContext:
    settings = get_settings()
    role = normalize_role(x_user_role or settings.default_role, settings.default_role)
    return UserContext(user_id=x_user_id or "enterprise.user", role=role, session_id=x_session_id)


def get_services(request: Request) -> ServiceRegistry:
    services = getattr(request.app.state, "services", None)
    if services is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Services unavailable")
    return services
