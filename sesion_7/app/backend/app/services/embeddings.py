"""Embeddings con cache + batching.

Pasos:
1. Buscar cada texto en la cache.
2. De-duplicar los que faltan (si el mismo texto llega 5 veces, se calcula 1 vez).
3. Enviar TODOS los faltantes al backend en UNA sola llamada (batching).
4. Guardar en cache y devolver los vectores en el orden original.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from app.services.cache import EmbeddingCache
from app.services.ollama_client import LLMBackend


@dataclass
class EmbedResult:
    vectors: list[list[float]]
    hits: int
    misses: int
    unique_embedded: int
    latency_ms: float


async def embed_with_cache(backend: LLMBackend, cache: EmbeddingCache, model: str, texts: list[str]) -> EmbedResult:
    t0 = time.perf_counter()
    cached = cache.get_many(model, texts)
    missing_idx = [i for i in range(len(texts)) if i not in cached]

    unique_missing: list[str] = []
    seen: dict[str, int] = {}
    for i in missing_idx:
        if texts[i] not in seen:
            seen[texts[i]] = len(unique_missing)
            unique_missing.append(texts[i])

    new_vectors: list[list[float]] = []
    if unique_missing:
        new_vectors = await backend.embed(model, unique_missing)
        cache.put_many(model, unique_missing, new_vectors)

    out: list[list[float]] = []
    for i, t in enumerate(texts):
        out.append(cached[i] if i in cached else new_vectors[seen[t]])
    return EmbedResult(
        vectors=out,
        hits=len(cached),
        misses=len(missing_idx),
        unique_embedded=len(unique_missing),
        latency_ms=round((time.perf_counter() - t0) * 1000, 2),
    )
