"""Proveedor Ollama (inferencia local).

Usa la API REST nativa de Ollama (`/api/chat`). Los tiempos que devuelve
Ollama vienen en nanosegundos; aquí se convierten a segundos.
Referencia: https://docs.ollama.com/api/usage
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from ..schemas import ChatMessage
from .base import ChatResult, ProviderError, StreamEvent

_NS = 1_000_000_000


class OllamaProvider:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_s: float = 120.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.model = model
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout_s, connect=5.0),
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def _payload(
        self,
        messages: list[ChatMessage],
        *,
        max_tokens: int,
        temperature: float,
        stream: bool,
    ) -> dict:
        return {
            "model": self.model,
            "stream": stream,
            "messages": [m.model_dump() for m in messages],
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }

    @staticmethod
    def _result(data: dict, content: str, model: str) -> ChatResult:
        return ChatResult(
            content=content,
            model=data.get("model", model),
            prompt_tokens=int(data.get("prompt_eval_count", 0)),
            completion_tokens=int(data.get("eval_count", 0)),
            total_duration_s=data.get("total_duration", 0) / _NS,
            eval_duration_s=data.get("eval_duration", 0) / _NS,
        )

    async def chat(
        self, messages: list[ChatMessage], *, max_tokens: int, temperature: float
    ) -> ChatResult:
        payload = self._payload(
            messages, max_tokens=max_tokens, temperature=temperature, stream=False
        )
        try:
            resp = await self._client.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(f"Fallo al consultar Ollama: {exc}") from exc
        content = (data.get("message") or {}).get("content", "")
        return self._result(data, content, self.model)

    async def stream(
        self, messages: list[ChatMessage], *, max_tokens: int, temperature: float
    ) -> AsyncIterator[StreamEvent]:
        payload = self._payload(
            messages, max_tokens=max_tokens, temperature=temperature, stream=True
        )
        parts: list[str] = []
        try:
            async with self._client.stream("POST", "/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    text = (data.get("message") or {}).get("content", "")
                    if text:
                        parts.append(text)
                        yield StreamEvent(text=text)
                    if data.get("done"):
                        yield StreamEvent(
                            done=True,
                            result=self._result(data, "".join(parts), self.model),
                        )
                        return
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(f"Fallo en streaming con Ollama: {exc}") from exc

    async def health(self) -> bool:
        try:
            resp = await self._client.get("/api/tags", timeout=3.0)
            return resp.status_code == 200
        except httpx.HTTPError:
            return False
