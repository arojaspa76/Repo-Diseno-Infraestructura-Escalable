"""Cliente asíncrono para Ollama.

Se define un ``Protocol`` (``LLMBackend``) para que el resto de la aplicación no
dependa de Ollama: en las pruebas se usa un backend falso y, en el futuro, se
podría añadir un backend para vLLM o para un endpoint administrado.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx


class BackendError(RuntimeError):
    """Error al hablar con el backend de inferencia."""


@dataclass
class TokenEvent:
    text: str


@dataclass
class FinalEvent:
    """Estadísticas finales. Las duraciones de Ollama vienen en nanosegundos."""

    stats: dict[str, Any] = field(default_factory=dict)


StreamEvent = TokenEvent | FinalEvent


class LLMBackend(Protocol):
    def chat_stream(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        options: dict[str, Any],
        keep_alive: str | int | None,
    ) -> AsyncIterator[StreamEvent]: ...

    async def embed(self, model: str, inputs: list[str]) -> list[list[float]]: ...

    async def list_models(self) -> list[dict[str, Any]]: ...

    async def ping(self) -> bool: ...

    async def aclose(self) -> None: ...


class OllamaClient:
    def __init__(self, base_url: str, timeout_s: float = 120.0, http: httpx.AsyncClient | None = None) -> None:
        self._http = http or httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout_s, connect=5.0),
        )

    async def chat_stream(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        options: dict[str, Any],
        keep_alive: str | int | None = None,
    ) -> AsyncIterator[StreamEvent]:
        payload: dict[str, Any] = {"model": model, "messages": messages, "stream": True, "options": options}
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive
        try:
            async with self._http.stream("POST", "/api/chat", json=payload) as resp:
                if resp.status_code != 200:
                    body = (await resp.aread()).decode("utf-8", errors="replace")[:500]
                    raise BackendError(f"Ollama respondió {resp.status_code}: {body}")
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    if "error" in data:
                        raise BackendError(str(data["error"]))
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield TokenEvent(content)
                    if data.get("done"):
                        yield FinalEvent(stats=data)
        except httpx.HTTPError as exc:
            raise BackendError(f"No se pudo contactar a Ollama: {exc}") from exc

    async def embed(self, model: str, inputs: list[str]) -> list[list[float]]:
        """Embeddings en lote: Ollama acepta una lista en ``input`` (batching real)."""
        try:
            resp = await self._http.post("/api/embed", json={"model": model, "input": inputs})
        except httpx.HTTPError as exc:
            raise BackendError(f"No se pudo contactar a Ollama: {exc}") from exc
        if resp.status_code != 200:
            raise BackendError(f"Ollama /api/embed respondió {resp.status_code}: {resp.text[:300]}")
        embeddings = resp.json().get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(inputs):
            raise BackendError("Respuesta de embeddings inesperada")
        return embeddings

    async def list_models(self) -> list[dict[str, Any]]:
        try:
            resp = await self._http.get("/api/tags")
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise BackendError(f"No se pudo listar modelos: {exc}") from exc
        return list(resp.json().get("models", []))

    async def ping(self) -> bool:
        try:
            resp = await self._http.get("/api/version", timeout=3.0)
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def aclose(self) -> None:
        await self._http.aclose()
