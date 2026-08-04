import pytest

from app.core.exceptions import (
    AppException,
    ConfigurationError,
    ConflictError,
    DatabaseError,
    DownloadError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    ProviderError,
    QueueError,
    RateLimitError,
    UnauthorizedError,
    ValidationError,
    get_status_code,
)


class TestExceptions:
    def test_app_exception_base(self):
        exc = AppException(
            "Test error", code="TEST_ERROR", status_code=400, details={"key": "value"}
        )
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.code == "TEST_ERROR"
        assert exc.status_code == 400
        assert exc.details == {"key": "value"}

    def test_validation_error(self):
        exc = ValidationError("Invalid input", details={"field": "email"})
        assert exc.code == "VALIDATION_ERROR"
        assert exc.status_code == 400
        assert exc.details == {"field": "email"}

    def test_not_found_error(self):
        exc = NotFoundError("User not found", details={"user_id": 123})
        assert exc.code == "NOT_FOUND"
        assert exc.status_code == 404
        assert exc.details == {"user_id": 123}

    def test_unauthorized_error(self):
        exc = UnauthorizedError("Invalid token")
        assert exc.code == "UNAUTHORIZED"
        assert exc.status_code == 401

    def test_forbidden_error(self):
        exc = ForbiddenError("Access denied")
        assert exc.code == "FORBIDDEN"
        assert exc.status_code == 403

    def test_conflict_error(self):
        exc = ConflictError("Already exists")
        assert exc.code == "CONFLICT"
        assert exc.status_code == 409

    def test_rate_limit_error(self):
        exc = RateLimitError("Too many requests", retry_after=60)
        assert exc.code == "RATE_LIMITED"
        assert exc.status_code == 429
        assert exc.details["retry_after"] == 60

    def test_provider_error(self):
        exc = ProviderError("YouTube API error", provider="youtube", details={"status": 403})
        assert exc.code == "PROVIDER_ERROR"
        assert exc.status_code == 502
        assert exc.details["provider"] == "youtube"
        assert exc.details["status"] == 403

    def test_download_error(self):
        exc = DownloadError(
            "Download failed", download_id="dl_123", details={"url": "http://example.com"}
        )
        assert exc.code == "DOWNLOAD_ERROR"
        assert exc.status_code == 500
        assert exc.details["download_id"] == "dl_123"
        assert exc.details["url"] == "http://example.com"

    def test_queue_error(self):
        exc = QueueError("Queue full", details={"queue_size": 100})
        assert exc.code == "QUEUE_ERROR"
        assert exc.status_code == 503

    def test_configuration_error(self):
        exc = ConfigurationError("Missing config", details={"key": "DATABASE_URL"})
        assert exc.code == "CONFIGURATION_ERROR"
        assert exc.status_code == 500

    def test_database_error(self):
        exc = DatabaseError("Connection failed", details={"host": "localhost"})
        assert exc.code == "DATABASE_ERROR"
        assert exc.status_code == 500

    def test_external_service_error(self):
        exc = ExternalServiceError("Service unavailable", service="redis", details={"timeout": 5})
        assert exc.code == "EXTERNAL_SERVICE_ERROR"
        assert exc.status_code == 502
        assert exc.details["service"] == "redis"

    def test_get_status_code_mapping(self):
        assert get_status_code(ValidationError("test")) == 400
        assert get_status_code(UnauthorizedError("test")) == 401
        assert get_status_code(ForbiddenError("test")) == 403
        assert get_status_code(NotFoundError("test")) == 404
        assert get_status_code(ConflictError("test")) == 409
        assert get_status_code(RateLimitError("test")) == 429
        assert get_status_code(ProviderError("test", "yt")) == 502
        assert get_status_code(DownloadError("test")) == 500
        assert get_status_code(QueueError("test")) == 503
        assert get_status_code(ConfigurationError("test")) == 500
        assert get_status_code(DatabaseError("test")) == 500
        assert get_status_code(ExternalServiceError("test", "svc")) == 502
        assert get_status_code(Exception("unknown")) == 500