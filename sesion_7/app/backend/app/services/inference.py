"""Orquestación de una inferencia: guardrails → backend → métricas.

Aquí se miden las métricas que se estudian en la sesión:

* TTFT  (Time To First Token): tiempo desde que llega la petición hasta el primer token.
        Incluye cola, carga del modelo (cold start) y *prefill* del prompt.
* TPOT  (Time Per Output Token): tiempo medio entre tokens en la fase *decode*.
* Throughput de decode: tokens/segundo reportados por el backend.
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.config import Settings
from app.schemas import ChatRequest, GuardInfo, InferenceMetrics
from app.services.metrics import MetricsStore
from app.services.ollama_client import FinalEvent, LLMBackend, TokenEvent
from app.services.security import inspect_text, sanitize_output


class GuardBlocked(Exception):
    def __init__(self, guard: GuardInfo) -> None:
        super().__init__("; ".join(guard.reasons))
        self.guard = guard


@dataclass
class PreparedChat:
    model: str
    messages: list[dict[str, str]]
    options: dict[str, object]
    guard: GuardInfo


def prepare_chat(req: ChatRequest, settings: Settings, metrics: MetricsStore) -> PreparedChat:
    """Aplica política de mensajes + guardrails. Lanza GuardBlocked si corresponde."""
    model = req.model or settings.default_model
    messages: list[dict[str, str]] = [{"role": "system", "content": settings.system_prompt}]
    worst = GuardInfo(injection_score=0, injection_matches=[], pii_found={}, blocked=False, reasons=[])

    for m in req.messages:
        if m.role == "system" and not settings.allow_client_system:
            continue  # el cliente no controla el prompt de sistema (reduce prompt injection directa)
        content = m.content
        if m.role == "user" and settings.guard_mode != "off":
            guard, redacted = inspect_text(content, settings)
            if guard.injection_score >= worst.injection_score:
                worst = guard.model_copy(update={"pii_found": {**worst.pii_found, **guard.pii_found}})
            if guard.blocked:
                metrics.record_block()
                raise GuardBlocked(guard)
            content = redacted  # la PII se redacta ANTES de salir hacia el modelo
        messages.append({"role": m.role, "content": content})

    options: dict[str, object] = {
        "temperature": req.temperature,
        "num_predict": min(req.max_tokens, settings.max_output_tokens),
    }
    if req.num_ctx:
        options["num_ctx"] = req.num_ctx
    return PreparedChat(model=model, messages=messages, options=options, guard=worst)


def _ns_to_ms(v: object) -> float | None:
    return float(v) / 1e6 if isinstance(v, (int, float)) and v > 0 else None


async def run_chat_stream(
    backend: LLMBackend, prep: PreparedChat, keep_alive: str | int | None, metrics: MetricsStore
) -> AsyncIterator[TokenEvent | InferenceMetrics]:
    """Emite TokenEvent por cada fragmento y, al final, un InferenceMetrics."""
    start = time.perf_counter()
    t_first: float | None = None
    t_last: float | None = None
    n_chunks = 0
    final: dict[str, object] = {}
    try:
        async for ev in backend.chat_stream(
            model=prep.model, messages=prep.messages, options=prep.options, keep_alive=keep_alive
        ):
            if isinstance(ev, TokenEvent):
                now = time.perf_counter()
                if t_first is None:
                    t_first = now
                t_last = now
                n_chunks += 1
                yield ev
            elif isinstance(ev, FinalEvent):
                final = ev.stats
    except Exception:
        metrics.record_error()
        raise

    end = time.perf_counter()
    completion_tokens = int(final.get("eval_count", n_chunks) or n_chunks)
    tpot: float | None = None
    if t_first is not None and t_last is not None and completion_tokens > 1:
        tpot = (t_last - t_first) * 1000 / (completion_tokens - 1)
    eval_ms = _ns_to_ms(final.get("eval_duration"))
    m = InferenceMetrics(
        model=prep.model,
        ttft_ms=round((t_first - start) * 1000, 2) if t_first is not None else None,
        tpot_ms=round(tpot, 2) if tpot is not None else None,
        total_ms=round((end - start) * 1000, 2),
        prompt_tokens=int(final.get("prompt_eval_count", 0) or 0),
        completion_tokens=completion_tokens,
        decode_tokens_per_s=round(completion_tokens / (eval_ms / 1000), 2) if eval_ms else None,
        prompt_eval_ms=round(_ns_to_ms(final.get("prompt_eval_duration")) or 0, 2) or None,
        load_ms=round(_ns_to_ms(final.get("load_duration")) or 0, 2) or None,
    )
    metrics.record(m)
    yield m


async def run_chat(
    backend: LLMBackend, prep: PreparedChat, keep_alive: str | int | None, metrics: MetricsStore
) -> tuple[str, InferenceMetrics]:
    parts: list[str] = []
    result: InferenceMetrics | None = None
    async for item in run_chat_stream(backend, prep, keep_alive, metrics):
        if isinstance(item, TokenEvent):
            parts.append(item.text)
        else:
            result = item
    assert result is not None
    return sanitize_output("".join(parts)), result
