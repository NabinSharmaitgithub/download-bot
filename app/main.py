from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

from app.api import router as api_router
from app.core.config import get_settings
from app.core.exceptions import AppException, get_status_code
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    setup_logging()
    logger.info("application_startup", version="0.1.0", env=settings.app_env)
    yield
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Download Bot API",
        description="Telegram download bot with multi-provider support",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        method = request.method
        endpoint = request.url.path

        with REQUEST_LATENCY.labels(method=method, endpoint=endpoint).time():
            response = await call_next(request)

        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status=response.status_code,
        ).inc()

        return response

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.error(
            "application_error",
            code=exc.code,
            message=exc.message,
            details=exc.details,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "unhandled_exception",
            error_type=type(exc).__name__,
            error_message=str(exc),
            path=request.url.path,
        )
        status_code = get_status_code(exc)
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                }
            },
        )

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/ready", tags=["health"])
    async def readiness_check() -> dict[str, str]:
        return {"status": "ready"}

    @app.get("/metrics", tags=["monitoring"])
    async def metrics() -> Response:
        return Response(content=generate_latest(), media_type="text/plain")

    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
