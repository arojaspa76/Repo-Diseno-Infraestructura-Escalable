"""Endpoints de chat: respuesta completa y respuesta en streaming (SSE)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.schemas import ChatRequest, ChatResponse, InferenceMetrics
from app.services.inference import GuardBlocked, prepare_chat, run_chat, run_chat_stream
from app.services.ollama_client import BackendError, TokenEvent
from app.services.security import make_auth_dependency, make_rate_limit_dependency

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
    dependencies=[Depends(make_auth_dependency()), Depends(make_rate_limit_dependency())],
)


def _sse(event: str, data: dict) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode()


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    state = request.app.state
    try:
        prep = prepare_chat(req, state.settings, state.metrics)
    except GuardBlocked as exc:
        raise HTTPException(422, detail={"error": "guardrail", "reasons": exc.guard.reasons}) from exc
    try:
        answer, metrics = await run_chat(state.backend, prep, req.keep_alive, state.metrics)
    except BackendError as exc:
        raise HTTPException(502, str(exc)) from exc
    return ChatResponse(answer=answer, metrics=metrics, guard=prep.guard)


@router.post("/stream")
async def chat_stream(req: ChatRequest, request: Request) -> StreamingResponse:
    """Streaming con Server-Sent Events: eventos ``token``, ``metrics`` y ``error``.

    El cliente recibe el primer token en cuanto existe (mejora la latencia *percibida*
    aunque el tiempo total sea el mismo).
    """
    state = request.app.state
    try:
        prep = prepare_chat(req, state.settings, state.metrics)
    except GuardBlocked as exc:
        raise HTTPException(422, detail={"error": "guardrail", "reasons": exc.guard.reasons}) from exc

    async def gen() -> AsyncIterator[bytes]:
        try:
            async for item in run_chat_stream(state.backend, prep, req.keep_alive, state.metrics):
                if isinstance(item, TokenEvent):
                    yield _sse("token", {"text": item.text})
                elif isinstance(item, InferenceMetrics):
                    yield _sse("metrics", item.model_dump())
        except BackendError as exc:
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
