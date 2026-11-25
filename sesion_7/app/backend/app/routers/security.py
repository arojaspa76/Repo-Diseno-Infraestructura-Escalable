"""Endpoint didáctico para ver los guardrails en acción (sin llamar al modelo)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.schemas import InspectRequest, InspectResponse
from app.services.security import inspect_text, make_auth_dependency, make_rate_limit_dependency

router = APIRouter(
    prefix="/api/security",
    tags=["seguridad"],
    dependencies=[Depends(make_auth_dependency()), Depends(make_rate_limit_dependency())],
)


@router.post("/inspect", response_model=InspectResponse)
async def inspect(req: InspectRequest, request: Request) -> InspectResponse:
    """Muestra qué detectaría el guardrail y cómo quedaría el texto tras redactar PII."""
    guard, redacted = inspect_text(req.text, request.app.state.settings)
    return InspectResponse(guard=guard, redacted_text=redacted)
