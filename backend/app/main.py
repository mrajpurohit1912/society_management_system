import uuid
import time
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.logging_context import set_logging_context, clear_logging_context
from app.authentication.routes import router as auth_router
from app.societies.routes import router as societies_router

# Initialize structured logging
setup_logging(env=settings.ENV, log_level=settings.LOG_LEVEL)
logger = structlog.get_logger(__name__)

# Initialize modern FastAPI app with OpenAPI configurations
app = FastAPI(
    title="Society Management System API",
    description="Enterprise API backend for society management and user authentication",
    version="1.0.0",
)

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Reset logging context for this request
    clear_logging_context()

    # Generate or propagate Correlation ID
    correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID") or str(uuid.uuid4())
    
    # Store request context
    client_ip = request.client.host if request.client else "unknown"
    set_logging_context(
        correlation_id=correlation_id,
        method=request.method,
        path=request.url.path,
        client_ip=client_ip
    )

    logger.info("request.started", query_params=str(request.query_params))
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Add correlation ID to response headers for tracking
        response.headers["X-Correlation-ID"] = correlation_id
        
        logger.info(
            "request.finished",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2)
        )
        return response
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.exception(
            "request.failed",
            error=str(exc),
            duration_ms=round(duration_ms, 2)
        )
        raise exc

import os

# Setup CORS (Cross-Origin Resource Sharing)
# Configure these origins according to production deployment domain
origins = [
    "http://localhost:3000",  # Default local React/Next.js port
    "http://127.0.0.1:3000",
    "http://localhost:4200",  # Angular/frontend development port
    "http://127.0.0.1:4200",
    "http://localhost:5114",
    "https://localhost:5114",
    "https://saclon-nsp.github.io",  # GitHub Pages deployed UI
]

allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    origins.extend([origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Feature Slices Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(societies_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Society Management System Backend is running."}

