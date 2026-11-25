"""Guardrails de primera capa para una aplicación LLM.

IMPORTANTE (honestidad académica): estas reglas son *heurísticas*. Detectan ataques
simples y sirven para enseñar el concepto de "defensa en capas", pero un atacante
decidido puede evadirlas. No sustituyen: privilegios mínimos, aislamiento de
herramientas, validación de salidas, revisión humana ni servicios administrados
de guardrails (Azure AI Content Safety / Prompt Shields, Bedrock Guardrails,
Model Armor en Google Cloud). Ver docs/04_seguridad_llm.md.
"""

from __future__ import annotations

import re
import secrets
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field

from fastapi import Header, HTTPException, Request, status

from app.config import Settings, get_settings
from app.schemas import GuardInfo

# ---------------------------------------------------------------- prompt injection
# (patrón, peso, etiqueta). Peso 3 = señal fuerte; 1 = señal débil.
_INJECTION_RULES: list[tuple[re.Pattern[str], int, str]] = [
    (re.compile(r"ignor(a|e|ar)\s+(todas?\s+)?(las\s+)?(instrucciones|reglas)\s*(anteriores|previas)?", re.I), 3, "ignora-instrucciones"),
    (re.compile(r"ignore\s+(all\s+|any\s+|the\s+)?(previous|prior|above)\s+(instructions|rules|prompts?)", re.I), 3, "ignore-previous"),
    (re.compile(r"(reveal|show|print|repeat|leak)\s+(me\s+)?(your|the)\s+(system\s+)?(prompt|instructions)", re.I), 3, "leak-system-prompt"),
    (re.compile(r"(revela|muestra|imprime|repite)\s+(tu|el)\s+(prompt|instrucciones)(\s+de\s+sistema)?", re.I), 3, "leak-system-prompt-es"),
    (re.compile(r"\b(DAN|developer\s+mode|modo\s+desarrollador|jailbreak)\b", re.I), 3, "jailbreak-keyword"),
    (re.compile(r"you\s+are\s+now\s+(a|an|the)\b", re.I), 1, "role-reassign"),
    (re.compile(r"(ahora\s+eres|a\s+partir\s+de\s+ahora\s+eres)\b", re.I), 1, "role-reassign-es"),
    (re.compile(r"(<\s*/?\s*system\s*>|\[\s*system\s*\]|###\s*system)", re.I), 2, "fake-system-tag"),
    (re.compile(r"(disregard|olvida)\s+(your|tus|todo)", re.I), 1, "disregard"),
]
_BLOCK_THRESHOLD = 3

# ---------------------------------------------------------------- PII y secretos
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)\d{3}[\s.-]?\d{3,4}(?!\d)")
_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
_ID_DOC = re.compile(r"\b(?:C\.?C\.?|c[eé]dula|NIT|DNI|pasaporte)\s*[:#]?\s*[\d.\-]{6,15}\b", re.I)
_SECRETS = [
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS_ACCESS_KEY"),
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"), "GOOGLE_API_KEY"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b"), "API_KEY"),
]


def _luhn_ok(number: str) -> bool:
    digits = [int(c) for c in re.sub(r"\D", "", number)]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def redact_pii(text: str) -> tuple[str, dict[str, int]]:
    """Reemplaza PII/secretos por etiquetas. Devuelve (texto, conteos)."""
    found: dict[str, int] = defaultdict(int)

    def sub(pattern: re.Pattern[str], label: str, s: str, validator=None) -> str:
        def repl(m: re.Match[str]) -> str:
            if validator is not None and not validator(m.group(0)):
                return m.group(0)
            found[label] += 1
            return f"[{label}]"

        return pattern.sub(repl, s)

    out = text
    for pat, label in _SECRETS:
        out = sub(pat, label, out)
    out = sub(_EMAIL, "EMAIL", out)
    out = sub(_ID_DOC, "DOCUMENTO_ID", out)
    out = sub(_CARD, "TARJETA", out, validator=_luhn_ok)
    out = sub(_PHONE, "TELEFONO", out)
    return out, dict(found)


def inspect_text(text: str, settings: Settings | None = None) -> tuple[GuardInfo, str]:
    """Analiza un texto. Devuelve (GuardInfo, texto_redactado)."""
    settings = settings or get_settings()
    matches: list[str] = []
    score = 0
    for pattern, weight, label in _INJECTION_RULES:
        if pattern.search(text):
            matches.append(label)
            score += weight
    redacted, pii = redact_pii(text)

    reasons: list[str] = []
    if len(text) > settings.max_input_chars:
        reasons.append(f"entrada demasiado larga (> {settings.max_input_chars} caracteres)")
    if score >= _BLOCK_THRESHOLD:
        reasons.append("posible prompt injection")
    blocked = bool(reasons) and settings.guard_mode == "block"
    return (
        GuardInfo(injection_score=score, injection_matches=matches, pii_found=pii, blocked=blocked, reasons=reasons),
        redacted,
    )


_MD_IMAGE = re.compile(r"!\[[^\]]*\]\((?:https?:)?//[^)]*\)")
_HTML_TAGS = re.compile(r"<\s*/?\s*(script|iframe|img|object|embed|style)[^>]*>", re.I)


def sanitize_output(text: str) -> str:
    """Neutraliza vectores típicos de exfiltración/XSS en la *salida* del modelo (OWASP: manejo inseguro de salidas)."""
    text = _MD_IMAGE.sub("[imagen externa eliminada]", text)
    return _HTML_TAGS.sub("", text)


# ---------------------------------------------------------------- autenticación y rate limit
def make_auth_dependency():
    """Dependencia FastAPI que valida ``X-API-Key`` con comparación de tiempo constante."""

    async def _dep(request: Request, x_api_key: str | None = Header(default=None)) -> None:
        settings: Settings = request.app.state.settings
        if settings.api_key is None:
            return
        if x_api_key is None or not secrets.compare_digest(x_api_key, settings.api_key):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key inválida o ausente")

    return _dep


@dataclass
class SlidingWindowRateLimiter:
    """Límite por ventana deslizante, en memoria. Con varias réplicas se necesita un almacén compartido (Redis)."""

    limit: int
    window_s: float = 60.0
    _hits: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def check(self, key: str, now: float | None = None) -> float:
        """Devuelve 0 si se permite; si no, los segundos de espera sugeridos."""
        now = time.monotonic() if now is None else now
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] >= self.window_s:
                q.popleft()
            if len(q) >= self.limit:
                return max(0.0, self.window_s - (now - q[0]))
            q.append(now)
            return 0.0


def make_rate_limit_dependency():
    async def _dep(request: Request, x_api_key: str | None = Header(default=None)) -> None:
        limiter: SlidingWindowRateLimiter = request.app.state.rate_limiter
        client = request.client.host if request.client else "unknown"
        key = f"key:{x_api_key}" if x_api_key else f"ip:{client}"
        wait = limiter.check(key)
        if wait > 0:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Límite de peticiones excedido",
                headers={"Retry-After": str(int(wait) + 1)},
            )

    return _dep
