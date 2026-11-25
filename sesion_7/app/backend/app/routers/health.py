"""Salud, modelos disponibles y métricas."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.services.ollama_client import BackendError
from app.services.security import make_auth_dependency

router = APIRouter()
_auth = make_auth_dependency()


@router.get("/health", tags=["salud"])
async def health() -> dict[str, str]:
    """Liveness: el proceso está vivo. No consulta dependencias."""
    return {"status": "ok"}


@router.get("/ready", tags=["salud"])
async def ready(request: Request) -> dict[str, str]:
    """Readiness: el backend de inferencia responde. Úselo como probe en Kubernetes."""
    if not await request.app.state.backend.ping():
        raise HTTPException(503, "El backend de inferencia (Ollama) no responde")
    return {"status": "ready"}


@router.get("/api/models", tags=["modelos"], dependencies=[Depends(_auth)])
async def models(request: Request) -> dict[str, object]:
    try:
        items = await request.app.state.backend.list_models()
    except BackendError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {
        "default_model": request.app.state.settings.default_model,
        "models": [{"name": m.get("name"), "size_bytes": m.get("size")} for m in items],
    }


@router.get("/api/metrics/summary", tags=["métricas"], dependencies=[Depends(_auth)])
async def metrics_summary(request: Request) -> dict[str, object]:
    summary = request.app.state.metrics.summary()
    summary["embedding_cache"] = request.app.state.cache.stats()
    return summary


@router.get("/metrics", tags=["métricas"], include_in_schema=False)
async def prometheus(request: Request) -> Response:
    """Formato Prometheus. En producción, restrinja el acceso por red (no por API key)."""
    cache = request.app.state.cache
    text = request.app.state.metrics.prometheus_text(cache.hits, cache.misses)
    return Response(text, media_type="text/plain; version=0.0.4")
