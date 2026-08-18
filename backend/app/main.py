"""FastAPI application entrypoint."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import settings
from app.core.errors import DomainError
from app.core.logging import configure_logging, get_logger

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log.info(
        "starting",
        environment=settings.environment,
        efile_provider=settings.efile_provider,
        extraction_model=settings.extraction_model,
    )
    yield
    log.info("stopping")


app = FastAPI(
    title="AccountingAI",
    description=(
        "Cross-border U.S. tax compliance for non-U.S. investors in U.S. real-estate "
        "partnerships."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def bind_request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message, **exc.detail},
    )


@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {"status": "ok", "environment": settings.environment}


app.include_router(api_router)
