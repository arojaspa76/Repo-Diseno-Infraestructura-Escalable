"""Contratos de la API (Pydantic v2)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    # El cliente solo envía mensajes de usuario/asistente; el prompt de sistema
    # lo controla el servidor (evita que el cliente lo sobreescriba).
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)
    max_tokens: int | None = Field(default=None, ge=1, le=4096)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)


class UsageInfo(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CostInfo(BaseModel):
    """Dos miradas del mismo consumo (ver docs/04-finops-llm.md)."""

    shadow_api_usd: float = Field(
        description="Costo hipotético si se hubiera usado una API administrada."
    )
    selfhosted_usd: float = Field(
        description="Costo de la infraestructura propia por el tiempo de cómputo."
    )


class LatencyInfo(BaseModel):
    total_s: float
    ttft_s: float | None = Field(
        default=None, description="Time To First Token (solo en streaming)."
    )
    tokens_per_s: float | None = None


class BudgetInfo(BaseModel):
    spent_usd: float
    limit_usd: float
    percent_used: float
    alert_level: int | None = Field(
        default=None, description="Umbral más alto alcanzado (50/80/100) o null."
    )
    blocked: bool


class SecurityInfo(BaseModel):
    pii_redactions: int = 0
    flags: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    request_id: str
    model: str
    content: str
    usage: UsageInfo
    cost: CostInfo
    latency: LatencyInfo
    budget: BudgetInfo
    security: SecurityInfo


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None
