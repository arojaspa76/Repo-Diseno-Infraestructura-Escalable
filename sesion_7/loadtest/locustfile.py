"""Prueba de carga del backend con Locust.

    pip install -r requirements-dev.txt
    locust -f loadtest/locustfile.py --host http://localhost:8000
    # abra http://localhost:8089 y defina usuarios y ritmo de llegada
    # o en modo sin interfaz:
    locust -f loadtest/locustfile.py --host http://localhost:8000 --headless -u 10 -r 2 -t 60s

Mide la latencia TOTAL de cada petición; el TTFT/TPOT por petición los reporta el propio backend en `metrics`.
Si define S07_API_KEY en el backend, exporte la misma variable aquí.
"""

from __future__ import annotations

import os
import random

from locust import HttpUser, between, task

PROMPTS = [
    "¿Qué es el KV cache?",
    "Explica la diferencia entre prefill y decode en una frase.",
    "Da tres técnicas para reducir la latencia de un LLM.",
]


class ChatUser(HttpUser):
    wait_time = between(1, 3)  # tiempo de "lectura" del usuario entre preguntas

    def on_start(self) -> None:
        key = os.environ.get("S07_API_KEY")
        if key:
            self.client.headers["X-API-Key"] = key

    @task(5)
    def chat(self) -> None:
        self.client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": random.choice(PROMPTS)}], "max_tokens": 64},
            name="POST /api/chat",
        )

    @task(1)
    def embeddings(self) -> None:
        self.client.post("/api/embeddings", json={"texts": random.sample(PROMPTS, 2)}, name="POST /api/embeddings")

    @task(1)
    def health(self) -> None:
        self.client.get("/health", name="GET /health")
