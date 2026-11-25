"""Aplicación FastAPI de la Sesión 7.

Se usa una *fábrica* (``create_app``) para poder inyectar un backend falso en las pruebas.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import Settings, get_settings
from app.routers import capacity, chat, embeddings, health, security
from app.services.cache import EmbeddingCache
from app.services.metrics import MetricsStore
from app.services.ollama_client import LLMBackend, OllamaClient
from app.services.security import SlidingWindowRateLimiter

logger = logging.getLogger("s07")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for k in ("request_id", "path", "status", "duration_ms"):
            if hasattr(record, k):
                payload[k] = getattr(record, k)
        return json.dumps(payload, ensure_ascii=False)


def _configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger("s07")
    root.handlers = [handler]
    root.setLevel(level.upper())
    root.propagate = False


def _maybe_enable_otel(app: FastAPI, settings: Settings) -> None:
    if not settings.otel_enabled:
        return
    try:  # dependencias opcionales: pip install -r requirements-otel.txt
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        logger.info("OpenTelemetry habilitado")
    except ImportError:
        logger.warning("S07_OTEL_ENABLED=true pero faltan paquetes opentelemetry-*; se omite")


def create_app(settings: Settings | None = None, backend: LLMBackend | None = None) -> FastAPI:
    settings = settings or get_settings()
    _configure_logging(settings.log_level)

    app = FastAPI(
        title="Sesión 7 — Optimización de latencia y throughput en LLMs",
        version=__version__,
        description="Backend didáctico: streaming, métricas TTFT/TPOT, cache de embeddings, guardrails y estimador de capacidad.",
    )
    app.state.settings = settings
    app.state.backend = backend or OllamaClient(settings.ollama_base_url, settings.request_timeout_s)
    app.state.metrics = MetricsStore()
    app.state.cache = EmbeddingCache(settings.cache_db_path, settings.cache_max_entries)
    app.state.rate_limiter = SlidingWindowRateLimiter(limit=settings.rate_limit_per_minute)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        t0 = time.perf_counter()
        response = await call_next(request)
        dur = (time.perf_counter() - t0) * 1000
        response.headers["X-Request-ID"] = rid
        response.headers["X-Process-Time-ms"] = f"{dur:.1f}"
        # Nunca se registra el contenido de los prompts (privacidad): solo metadatos.
        logger.info(
            "request",
            extra={"request_id": rid, "path": request.url.path, "status": response.status_code, "duration_ms": round(dur, 1)},
        )
        return response

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(embeddings.router)
    app.include_router(security.router)
    app.include_router(capacity.router)

    _maybe_enable_otel(app, settings)
    return app


@asynccontextmanager
async def _lifespan(app: FastAPI):
    yield
    await app.state.backend.aclose()
    app.state.cache.close()


def build_app() -> FastAPI:
    app = create_app()
    app.router.lifespan_context = _lifespan
    return app


app = build_app()
