import json

import httpx
import pytest

from app.providers import OllamaProvider
from app.providers.base import ProviderError
from app.schemas import ChatMessage

MSGS = [ChatMessage(role="user", content="hola")]


def _provider(handler):
    return OllamaProvider("http://ollama.test", "m", transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_chat_parses_tokens_and_converts_ns_to_seconds():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["stream"] is False and body["options"]["num_predict"] == 64
        return httpx.Response(
            200,
            json={
                "model": "m",
                "message": {"role": "assistant", "content": "hola!"},
                "done": True,
                "prompt_eval_count": 11,
                "eval_count": 18,
                "total_duration": 2_000_000_000,
                "eval_duration": 1_000_000_000,
            },
        )

    res = await _provider(handler).chat(MSGS, max_tokens=64, temperature=0.1)
    assert (res.prompt_tokens, res.completion_tokens) == (11, 18)
    assert res.total_duration_s == 2.0 and res.eval_duration_s == 1.0


@pytest.mark.asyncio
async def test_stream_parses_ndjson():
    lines = [
        {"message": {"content": "ho"}, "done": False},
        {"message": {"content": "la"}, "done": False},
        {"message": {"content": ""}, "done": True, "prompt_eval_count": 3, "eval_count": 2,
         "total_duration": 1_000_000_000, "eval_duration": 500_000_000},
    ]
    payload = "\n".join(json.dumps(x) for x in lines)

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=payload.encode())

    events = [e async for e in _provider(handler).stream(MSGS, max_tokens=8, temperature=0)]
    assert "".join(e.text for e in events if not e.done) == "hola"
    assert events[-1].done and events[-1].result.content == "hola"
    assert events[-1].result.completion_tokens == 2


@pytest.mark.asyncio
async def test_http_error_becomes_provider_error():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    with pytest.raises(ProviderError):
        await _provider(handler).chat(MSGS, max_tokens=8, temperature=0)


@pytest.mark.asyncio
async def test_health_false_when_unreachable():
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route")

    assert await _provider(handler).health() is False
