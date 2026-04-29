from dataclasses import dataclass
from typing import Iterable


VALID_ROLES = {"viewer", "analyst", "manager", "admin"}
UPLOAD_ROLES = {"analyst", "manager", "admin"}


@dataclass(slots=True)
class UserContext:
    user_id: str
    role: str
    session_id: str | None = None


def normalize_role(role: str, default_role: str) -> str:
    normalized = (role or default_role).strip().lower()
    return normalized if normalized in VALID_ROLES else default_role


def can_upload(role: str) -> bool:
    return role in UPLOAD_ROLES


def is_authorized_for_roles(user_role: str, allowed_roles: Iterable[str]) -> bool:
    normalized = {role.strip().lower() for role in allowed_roles if role.strip()}
    return not normalized or user_role in normalized or user_role == "admin"
