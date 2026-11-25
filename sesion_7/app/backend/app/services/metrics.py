"""Almacén de métricas en memoria + exportación en formato Prometheus.

Es deliberadamente simple (ring buffer en memoria) para que se entienda.
En producción se exportaría a OpenTelemetry / Prometheus / el servicio nativo del cloud.
"""

from __future__ import annotations

import math
import threading
from collections import deque
from dataclasses import dataclass, field

from app.schemas import InferenceMetrics


def percentile(values: list[float], p: float) -> float | None:
    """Percentil por método de rango más cercano (nearest-rank). ``p`` en [0, 100]."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(p / 100 * len(ordered)))
    return ordered[rank - 1]


@dataclass
class MetricsStore:
    maxlen: int = 1000
    _records: deque[InferenceMetrics] = field(init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    requests_total: int = 0
    errors_total: int = 0
    guard_blocked_total: int = 0

    def __post_init__(self) -> None:
        self._records = deque(maxlen=self.maxlen)

    def record(self, m: InferenceMetrics) -> None:
        with self._lock:
            self._records.append(m)
            self.requests_total += 1

    def record_error(self) -> None:
        with self._lock:
            self.errors_total += 1

    def record_block(self) -> None:
        with self._lock:
            self.guard_blocked_total += 1

    def summary(self) -> dict[str, object]:
        with self._lock:
            records = list(self._records)

        def col(name: str) -> list[float]:
            return [v for r in records if (v := getattr(r, name)) is not None]

        def stats(name: str) -> dict[str, float | None]:
            vals = col(name)
            return {
                "p50": percentile(vals, 50),
                "p95": percentile(vals, 95),
                "p99": percentile(vals, 99),
                "mean": (sum(vals) / len(vals)) if vals else None,
            }

        return {
            "window_size": len(records),
            "requests_total": self.requests_total,
            "errors_total": self.errors_total,
            "guard_blocked_total": self.guard_blocked_total,
            "ttft_ms": stats("ttft_ms"),
            "tpot_ms": stats("tpot_ms"),
            "total_ms": stats("total_ms"),
            "decode_tokens_per_s": stats("decode_tokens_per_s"),
        }

    def prometheus_text(self, cache_hits: int = 0, cache_misses: int = 0) -> str:
        s = self.summary()
        lines = [
            "# HELP s07_requests_total Inferencias completadas",
            "# TYPE s07_requests_total counter",
            f"s07_requests_total {s['requests_total']}",
            "# HELP s07_errors_total Inferencias con error",
            "# TYPE s07_errors_total counter",
            f"s07_errors_total {s['errors_total']}",
            "# HELP s07_guard_blocked_total Peticiones bloqueadas por guardrails",
            "# TYPE s07_guard_blocked_total counter",
            f"s07_guard_blocked_total {s['guard_blocked_total']}",
            "# HELP s07_embedding_cache_hits_total Aciertos de cache de embeddings",
            "# TYPE s07_embedding_cache_hits_total counter",
            f"s07_embedding_cache_hits_total {cache_hits}",
            f"s07_embedding_cache_misses_total {cache_misses}",
        ]
        for name in ("ttft_ms", "tpot_ms", "total_ms"):
            st = s[name]
            assert isinstance(st, dict)
            lines.append(f"# TYPE s07_{name} gauge")
            for q in ("p50", "p95", "p99"):
                v = st[q]
                if v is not None:
                    lines.append(f's07_{name}{{quantile="{q}"}} {v:.3f}')
        return "\n".join(lines) + "\n"
