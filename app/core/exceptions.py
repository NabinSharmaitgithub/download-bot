from typing import Any


class AppException(Exception):
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ValidationError(AppException):
    def __init__(
        self,
        message: str = "Validation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details,
        )


class NotFoundError(AppException):
    def __init__(
        self,
        message: str = "Resource not found",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details,
        )


class UnauthorizedError(AppException):
    def __init__(
        self,
        message: str = "Unauthorized",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
            details=details,
        )


class ForbiddenError(AppException):
    def __init__(
        self,
        message: str = "Forbidden",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            details=details,
        )


class ConflictError(AppException):
    def __init__(
        self,
        message: str = "Resource conflict",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details,
        )


class RateLimitError(AppException):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="RATE_LIMITED",
            status_code=429,
            details={**(details or {}), "retry_after": retry_after},
        )


class ProviderError(AppException):
    def __init__(
        self,
        message: str,
        provider: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="PROVIDER_ERROR",
            status_code=502,
            details={**(details or {}), "provider": provider},
        )


class DownloadError(AppException):
    def __init__(
        self,
        message: str,
        download_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="DOWNLOAD_ERROR",
            status_code=500,
            details={**(details or {}), "download_id": download_id},
        )


class QueueError(AppException):
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="QUEUE_ERROR",
            status_code=503,
            details=details,
        )


class ConfigurationError(AppException):
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            status_code=500,
            details=details,
        )


class DatabaseError(AppException):
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500,
            details=details,
        )


class ExternalServiceError(AppException):
    def __init__(
        self,
        message: str,
        service: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={**(details or {}), "service": service},
        )


EXCEPTION_MAP: dict[type[AppException], int] = {
    ValidationError: 400,
    UnauthorizedError: 401,
    ForbiddenError: 403,
    NotFoundError: 404,
    ConflictError: 409,
    RateLimitError: 429,
    ProviderError: 502,
    DownloadError: 500,
    QueueError: 503,
    ConfigurationError: 500,
    DatabaseError: 500,
    ExternalServiceError: 502,
}


def get_status_code(exc: Exception) -> int:
    for exc_type, status_code in EXCEPTION_MAP.items():
        if isinstance(exc, exc_type):
            return status_code
    return 500
