"""Logging estructurado y métricas mínimas en formato Prometheus.

* Los logs son JSON (una línea por evento) -> los ingiere CloudWatch Logs,
  Azure Monitor o Cloud Logging sin parseo adicional.
* NUNCA se registra el contenido de prompts/respuestas salvo LOG_PROMPTS=true.
* Las métricas se exponen en `/metrics` (texto Prometheus). Para producción se
  recomienda OpenTelemetry (ver docs/04-finops-llm.md, sección Observabilidad).
"""

from __future__ import annotations

import json
import logging
import threading
from collections import defaultdict

_BUCKETS = (0.25, 0.5, 1, 2, 5, 10, 30, 60)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        extra = getattr(record, "event", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("gateway")
    logger.setLevel(level.upper())
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger


def log_event(logger: logging.Logger, msg: str, **fields: object) -> None:
    logger.info(msg, extra={"event": fields})


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
        self._hist_counts: dict[str, list[int]] = {}
        self._hist_sum: dict[str, float] = defaultdict(float)

    def inc(self, name: str, value: float = 1.0, **labels: str) -> None:
        key = (name, tuple(sorted(labels.items())))
        with self._lock:
            self._counters[key] += value

    def observe(self, name: str, value: float) -> None:
        with self._lock:
            counts = self._hist_counts.setdefault(name, [0] * (len(_BUCKETS) + 1))
            for i, bound in enumerate(_BUCKETS):
                if value <= bound:
                    counts[i] += 1
            counts[-1] += 1  # +Inf
            self._hist_sum[name] += value

    def render(self) -> str:
        lines: list[str] = []
        with self._lock:
            for (name, labels), value in sorted(self._counters.items()):
                label_txt = (
                    "{" + ",".join(f'{k}="{v}"' for k, v in labels) + "}" if labels else ""
                )
                lines.append(f"{name}{label_txt} {value}")
            for name, counts in sorted(self._hist_counts.items()):
                for bound, c in zip(_BUCKETS, counts, strict=False):
                    lines.append(f'{name}_bucket{{le="{bound}"}} {c}')
                lines.append(f'{name}_bucket{{le="+Inf"}} {counts[-1]}')
                lines.append(f"{name}_sum {self._hist_sum[name]}")
                lines.append(f"{name}_count {counts[-1]}")
        return "\n".join(lines) + "\n"
