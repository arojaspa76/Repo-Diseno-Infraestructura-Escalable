"""Embeddings con cache y batching."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.schemas import EmbedRequest, EmbedResponse
from app.services.embeddings import embed_with_cache
from app.services.ollama_client import BackendError
from app.services.security import make_auth_dependency, make_rate_limit_dependency

router = APIRouter(
    prefix="/api/embeddings",
    tags=["embeddings"],
    dependencies=[Depends(make_auth_dependency()), Depends(make_rate_limit_dependency())],
)


@router.post("", response_model=EmbedResponse)
async def embed(req: EmbedRequest, request: Request) -> EmbedResponse:
    state = request.app.state
    model = req.model or state.settings.embed_model
    if any(len(t) > state.settings.max_input_chars for t in req.texts):
        raise HTTPException(422, f"Cada texto debe tener ≤ {state.settings.max_input_chars} caracteres")
    try:
        result = await embed_with_cache(state.backend, state.cache, model, req.texts)
    except BackendError as exc:
        raise HTTPException(502, str(exc)) from exc
    return EmbedResponse(
        model=model,
        dimensions=len(result.vectors[0]),
        vectors=result.vectors,
        cache_hits=result.hits,
        cache_misses=result.misses,
        unique_texts_embedded=result.unique_embedded,
        latency_ms=result.latency_ms,
    )


@router.get("/cache/stats")
async def cache_stats(request: Request) -> dict[str, float | int]:
    return request.app.state.cache.stats()


@router.delete("/cache")
async def cache_clear(request: Request) -> dict[str, str]:
    request.app.state.cache.clear()
    return {"status": "cleared"}
