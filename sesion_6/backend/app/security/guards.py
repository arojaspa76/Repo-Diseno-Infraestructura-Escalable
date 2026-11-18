"""Controles de seguridad para aplicaciones LLM.

IMPORTANTE (honestidad técnica): estos controles son *defensa en capas*, no una
bala de plata. Las heurísticas de prompt injection se evaden con facilidad; su
valor es didáctico y como primera barrera barata. La mitigación real combina
mínimo privilegio, aislamiento de herramientas, validación de salida y
monitoreo. Ver docs/03-seguridad-llm.md (mapeo a OWASP LLM Top 10 2026).
"""

from __future__ import annotations

import hashlib
import hmac
import re
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# 1. Autenticación por API key (comparación en tiempo constante)
# ---------------------------------------------------------------------------


def authenticate(provided: str | None, valid_keys: list[str]) -> str | None:
    """Devuelve un client_id estable (hash corto) o None si no es válida.

    Con `valid_keys` vacío (solo dev) se acepta todo como cliente "dev".
    """
    if not valid_keys:
        return "dev"
    if not provided:
        return None
    for key in valid_keys:
        if hmac.compare_digest(provided.encode(), key.encode()):
            return hashlib.sha256(key.encode()).hexdigest()[:12]
    return None


# ---------------------------------------------------------------------------
# 2. Heurística de prompt injection (LLM01)
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "override_instructions",
        re.compile(
            r"(ignore|disregard|forget)\s+(all\s+|any\s+)?(the\s+)?"
            r"(previous|prior|above|earlier)\s+(instructions?|rules?|prompts?)",
            re.I,
        ),
    ),
    (
        "override_instructions",
        re.compile(
            r"(ignora|olvida|descarta)\s+(todas\s+)?(las\s+)?"
            r"(instrucciones|reglas|indicaciones)\s+(anteriores|previas)",
            re.I,
        ),
    ),
    (
        "reveal_system_prompt",
        re.compile(
            r"(reveal|show|print|repeat|leak)\s+(me\s+)?(your|the)\s+"
            r"(system\s+)?(prompt|instructions)",
            re.I,
        ),
    ),
    (
        "reveal_system_prompt",
        re.compile(
            r"(muestra|revela|imprime|repite)(me)?\s+(tu|el)\s+"
            r"(prompt|instrucciones)(\s+de\s+sistema)?",
            re.I,
        ),
    ),
    (
        "role_hijack",
        re.compile(
            r"(you\s+are\s+now|a\s+partir\s+de\s+ahora\s+eres|act\s+as\s+if\s+you\s+have\s+no)",
            re.I,
        ),
    ),
    (
        "jailbreak_keywords",
        re.compile(r"\b(DAN\s+mode|developer\s+mode|jailbreak)\b", re.I),
    ),
]


@dataclass
class InjectionReport:
    score: int = 0
    flags: list[str] = field(default_factory=list)


def scan_prompt_injection(text: str) -> InjectionReport:
    report = InjectionReport()
    for name, pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            report.score += 1
            if name not in report.flags:
                report.flags.append(name)
    return report


# ---------------------------------------------------------------------------
# 3. Redacción de datos personales antes de enviar al modelo (LLM02)
# ---------------------------------------------------------------------------

_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(\.[\w-]+)+\b")
_PHONE = re.compile(r"(?<!\d)(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}(?!\d)")
_DOCUMENT = re.compile(
    r"\b(cc|c\.c\.|cedula|cédula|nit|dni|ssn|pasaporte)\b[\s:#.]*\d[\d.\-]{5,}",
    re.I,
)
_CARD_CANDIDATE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        n = int(ch)
        if alt:
            n *= 2
            if n > 9:
                n -= 9
        total += n
        alt = not alt
    return total % 10 == 0


def redact_pii(text: str) -> tuple[str, int]:
    """Reemplaza emails, documentos, tarjetas (Luhn) y teléfonos. Devuelve (texto, n)."""
    count = 0

    def sub(pattern: re.Pattern[str], label: str, s: str) -> str:
        nonlocal count
        s, n = pattern.subn(label, s)
        count += n
        return s

    def card_sub(match: re.Match[str]) -> str:
        nonlocal count
        digits = re.sub(r"\D", "", match.group(0))
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            count += 1
            return "[TARJETA]"
        return match.group(0)

    text = sub(_EMAIL, "[EMAIL]", text)
    text = sub(_DOCUMENT, "[DOCUMENTO]", text)
    text = _CARD_CANDIDATE.sub(card_sub, text)
    text = sub(_PHONE, "[TELEFONO]", text)
    return text, count


# ---------------------------------------------------------------------------
# 4. Manejo seguro de la salida del modelo (LLM10)
# ---------------------------------------------------------------------------

_SCRIPT_BLOCK = re.compile(r"<\s*(script|iframe|object|embed)\b.*?<\s*/\s*\1\s*>", re.I | re.S)
_DANGEROUS_TAG = re.compile(r"<\s*/?\s*(script|iframe|object|embed|style)\b[^>]*>", re.I)
_EVENT_ATTR = re.compile(r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.I)
# Imágenes markdown con URL externa: vector clásico de exfiltración de datos.
_MD_EXTERNAL_IMAGE = re.compile(r"!\[[^\]]*\]\(\s*https?://[^)]*\)", re.I)


def sanitize_output(text: str) -> tuple[str, list[str]]:
    """Neutraliza contenido activo. Trata la salida del LLM como entrada no confiable."""
    flags: list[str] = []
    cleaned = _SCRIPT_BLOCK.sub("[contenido activo bloqueado]", text)
    cleaned = _DANGEROUS_TAG.sub("", cleaned)
    if cleaned != text:
        flags.append("active_content_removed")
    no_events = _EVENT_ATTR.sub("", cleaned)
    if no_events != cleaned:
        flags.append("event_handler_removed")
    cleaned = no_events
    no_img = _MD_EXTERNAL_IMAGE.sub("[imagen externa bloqueada]", cleaned)
    if no_img != cleaned:
        flags.append("external_image_blocked")
    return no_img, flags


# ---------------------------------------------------------------------------
# 5. Rate limiting por cliente (ventana deslizante) — LLM06 (consumo)
# ---------------------------------------------------------------------------


class SlidingWindowRateLimiter:
    def __init__(self, limit_per_minute: int, clock=time.monotonic) -> None:
        self._limit = limit_per_minute
        self._clock = clock
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, client_id: str) -> bool:
        now = self._clock()
        with self._lock:
            q = self._events[client_id]
            while q and now - q[0] >= 60.0:
                q.popleft()
            if len(q) >= self._limit:
                return False
            q.append(now)
            return True
