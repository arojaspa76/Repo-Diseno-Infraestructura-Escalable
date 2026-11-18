from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.providers.base import ChatResult, ProviderError, StreamEvent


class FakeProvider:
    """Proveedor determinista para pruebas: no necesita Ollama."""

    model = "fake-model"

    def __init__(self, reply: str = "Hola, soy un modelo de prueba.", fail: bool = False):
        self.reply = reply
        self.fail = fail
        self.calls: list[list] = []

    def _result(self) -> ChatResult:
        return ChatResult(
            content=self.reply,
            model=self.model,
            prompt_tokens=100,
            completion_tokens=50,
            total_duration_s=2.0,
            eval_duration_s=1.0,
        )

    async def chat(self, messages, *, max_tokens, temperature):
        self.calls.append(messages)
        if self.fail:
            raise ProviderError("caído")
        return self._result()

    async def stream(self, messages, *, max_tokens, temperature):
        self.calls.append(messages)
        if self.fail:
            raise ProviderError("caído")
        for word in self.reply.split(" "):
            yield StreamEvent(text=word + " ")
        yield StreamEvent(done=True, result=self._result())

    async def health(self) -> bool:
        return not self.fail


def make_settings(**overrides) -> Settings:
    base = dict(
        environment="dev",
        gateway_api_keys="",
        ref_price_input_per_mtok_usd=1.0,
        ref_price_output_per_mtok_usd=4.0,
        infra_cost_per_hour_usd=3.6,
        daily_budget_usd_per_client=0.01,
        rate_limit_per_minute=1000,
        _env_file=None,
    )
    base.update(overrides)
    return Settings(**base)


@pytest.fixture
def provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def client(provider):
    app = create_app(make_settings(), provider)
    with TestClient(app) as c:
        yield c
