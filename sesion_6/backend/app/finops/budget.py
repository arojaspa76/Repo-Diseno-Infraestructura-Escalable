"""Presupuesto diario por cliente con alertas por umbral.

Analogía con la nube: es el equivalente en la aplicación de un *Budget* de
AWS Budgets / Azure Cost Management / Cloud Billing. Y como ellos, avisa
en 50/80/100 %. La diferencia importante: aquí SÍ podemos bloquear
(hard limit), mientras que los budgets nativos solo notifican por defecto.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import date


@dataclass
class _Ledger:
    day: date
    spent_usd: float = 0.0
    tokens: int = 0
    highest_alert: int | None = None


@dataclass(frozen=True)
class BudgetStatus:
    spent_usd: float
    limit_usd: float
    percent_used: float
    alert_level: int | None
    blocked: bool
    new_alert: int | None = None  # umbral recién cruzado en esta operación


@dataclass
class BudgetTracker:
    limit_usd: float
    alert_levels: list[int] = field(default_factory=lambda: [50, 80, 100])
    _ledgers: dict[str, _Ledger] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def _ledger(self, client_id: str, today: date) -> _Ledger:
        led = self._ledgers.get(client_id)
        if led is None or led.day != today:
            led = _Ledger(day=today)
            self._ledgers[client_id] = led
        return led

    def _status(self, led: _Ledger, new_alert: int | None = None) -> BudgetStatus:
        pct = (led.spent_usd / self.limit_usd * 100.0) if self.limit_usd > 0 else 100.0
        return BudgetStatus(
            spent_usd=round(led.spent_usd, 8),
            limit_usd=self.limit_usd,
            percent_used=round(pct, 2),
            alert_level=led.highest_alert,
            blocked=pct >= 100.0,
            new_alert=new_alert,
        )

    def check(self, client_id: str, today: date | None = None) -> BudgetStatus:
        today = today or date.today()
        with self._lock:
            return self._status(self._ledger(client_id, today))

    def record(
        self, client_id: str, cost_usd: float, tokens: int, today: date | None = None
    ) -> BudgetStatus:
        if cost_usd < 0 or tokens < 0:
            raise ValueError("Costo y tokens no pueden ser negativos.")
        today = today or date.today()
        with self._lock:
            led = self._ledger(client_id, today)
            led.spent_usd += cost_usd
            led.tokens += tokens
            pct = (
                led.spent_usd / self.limit_usd * 100.0 if self.limit_usd > 0 else 100.0
            )
            crossed = [lvl for lvl in self.alert_levels if pct >= lvl]
            new_alert = None
            if crossed and (led.highest_alert is None or max(crossed) > led.highest_alert):
                led.highest_alert = max(crossed)
                new_alert = led.highest_alert
            return self._status(led, new_alert)
