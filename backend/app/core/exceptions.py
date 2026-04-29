from fastapi import status


class AppError(Exception):
    """Base application exception with API-friendly metadata."""

    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error_code: str = "app_error") -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code


class UpstreamServiceError(AppError):
    """Raised when an upstream dependency fails or times out."""

    def __init__(self, detail: str = "Upstream AI service is unavailable") -> None:
        super().__init__(
            detail=detail,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="upstream_service_error",
        )


class ResourceLimitError(AppError):
    """Raised when workload or payload limits are exceeded."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="resource_limit_exceeded",
        )