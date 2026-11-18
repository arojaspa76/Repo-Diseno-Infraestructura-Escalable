"""Interfaz de proveedor de inferencia.

El gateway depende de este contrato, no de Ollama. Para apuntar el mismo
gateway a Vertex AI, Foundry o Bedrock basta con implementar `LLMProvider`.
Esa es la idea de *desacoplar* (patrón Gateway / Anti-Corruption Layer).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

from ..schemas import ChatMessage


@dataclass(frozen=True)
class ChatResult:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_duration_s: float
    eval_duration_s: float  # tiempo de decodificación (generación de tokens)


@dataclass(frozen=True)
class StreamEvent:
    """Evento de streaming: un fragmento de texto o el evento final."""

    text: str = ""
    done: bool = False
    result: ChatResult | None = None  # solo presente cuando done=True


class ProviderError(RuntimeError):
    """Error del proveedor (red, timeout, respuesta inválida)."""


class LLMProvider(Protocol):
    model: str

    async def chat(
        self, messages: list[ChatMessage], *, max_tokens: int, temperature: float
    ) -> ChatResult: ...

    def stream(
        self, messages: list[ChatMessage], *, max_tokens: int, temperature: float
    ) -> AsyncIterator[StreamEvent]: ...

    async def health(self) -> bool: ...
