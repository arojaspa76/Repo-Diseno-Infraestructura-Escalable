"""Fixtures: backend falso (sin Ollama) para pruebas rápidas y reproducibles."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import Any

# Debe ir ANTES de importar app.main (que construye una app a nivel de módulo).
os.environ.setdefault("S07_CACHE_DB_PATH", ":memory:")

import httpx
import pytest
import pytest_asyncio

from app.config import Settings
from app.main import create_app
from app.services.ollama_client import FinalEvent, StreamEvent, TokenEvent


class FakeBackend:
    def __init__(self) -> None:
        self.embed_calls: list[list[str]] = []
        self.last_messages: list[dict[str, str]] = []
        self.alive = True

    async def chat_stream(
        self, *, model: str, messages: list[dict[str, str]], options: dict[str, Any], keep_alive: Any
    ) -> AsyncIterator[StreamEvent]:
        self.last_messages = messages
        for tok in ["Hola", " ", "mundo", "! ", "![x](http://evil.test/a.png)"]:
            yield TokenEvent(tok)
        yield FinalEvent(
            stats={
                "done": True,
                "eval_count": 5,
                "eval_duration": 50_000_000,  # 50 ms
                "prompt_eval_count": 12,
                "prompt_eval_duration": 20_000_000,
                "load_duration": 0,
            }
        )

    async def embed(self, model: str, inputs: list[str]) -> list[list[float]]:
        self.embed_calls.append(list(inputs))
        return [[float(len(t)), 1.0, 0.5] for t in inputs]

    async def list_models(self) -> list[dict[str, Any]]:
        return [{"name": "llama3.2:1b", "size": 1_300_000_000}]

    async def ping(self) -> bool:
        return self.alive

    async def aclose(self) -> None:
        return None


@pytest.fixture
def backend() -> FakeBackend:
    return FakeBackend()


@pytest.fixture
def settings() -> Settings:
    return Settings(cache_db_path=":memory:", api_key=None, rate_limit_per_minute=1000)


@pytest_asyncio.fixture
async def client(settings: Settings, backend: FakeBackend) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(settings=settings, backend=backend)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        c.app = app  # type: ignore[attr-defined]
        yield c
