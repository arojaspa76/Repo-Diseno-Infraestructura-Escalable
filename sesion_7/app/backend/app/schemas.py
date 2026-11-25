"""Contratos de la API (Pydantic v2)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=50)
    model: str | None = None
    temperature: float = Field(0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(256, ge=1, le=4096)
    num_ctx: int | None = Field(None, ge=256, le=131_072, description="Tamaño de ventana de contexto")
    keep_alive: str | int | None = Field(
        None, description="Cuánto tiempo queda el modelo en memoria (p. ej. '10m', -1)"
    )


class InferenceMetrics(BaseModel):
    """Métricas de una inferencia. Ver docs/02_conceptos_clave.md para el significado."""

    model: str
    ttft_ms: float | None = Field(None, description="Time To First Token medido en el servidor")
    tpot_ms: float | None = Field(None, description="Time Per Output Token (fase decode)")
    total_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    decode_tokens_per_s: float | None = Field(None, description="Velocidad de decode reportada por Ollama")
    prompt_eval_ms: float | None = Field(None, description="Duración del prefill reportada por Ollama")
    load_ms: float | None = Field(None, description="Tiempo de carga del modelo (cold start)")


class GuardInfo(BaseModel):
    injection_score: int
    injection_matches: list[str]
    pii_found: dict[str, int]
    blocked: bool
    reasons: list[str]


class ChatResponse(BaseModel):
    answer: str
    metrics: InferenceMetrics
    guard: GuardInfo


class EmbedRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=256)
    model: str | None = None


class EmbedResponse(BaseModel):
    model: str
    dimensions: int
    vectors: list[list[float]]
    cache_hits: int
    cache_misses: int
    unique_texts_embedded: int
    latency_ms: float


class InspectRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)


class InspectResponse(BaseModel):
    guard: GuardInfo
    redacted_text: str


class CapacityRequest(BaseModel):
    preset: str | None = Field(None, description="Nombre de un modelo de referencia (ver GET /api/capacity/presets)")
    params_billion: float | None = Field(None, gt=0)
    n_layers: int | None = Field(None, gt=0)
    n_kv_heads: int | None = Field(None, gt=0)
    head_dim: int | None = Field(None, gt=0)
    quant: str = "fp16"
    context_tokens: int = Field(4096, gt=0)
    concurrent_sequences: int = Field(1, gt=0)
    kv_dtype_bytes: float = Field(2.0, gt=0, description="2.0=FP16, 1.0=INT8/FP8")
    gpu_memory_gb: float | None = Field(None, gt=0)
    overhead_gb: float = Field(1.5, ge=0)


class CapacityResponse(BaseModel):
    weights_gb: float
    kv_cache_gb: float
    kv_cache_per_sequence_gb: float
    overhead_gb: float
    total_gb: float
    fits_in_gpu: bool | None
    max_sequences_that_fit: int | None
    notes: list[str]
