"""Cálculos FinOps (funciones puras, fáciles de probar)."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

from .catalog import Catalog, Instance

# ---------------------------------------------------------------------------
# 1. Capacidad
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CapacityPlan:
    requests_per_s: float
    needed_tokens_per_s: float
    instances_for_load: int
    instances_with_ha: int
    effective_tokens_per_s_per_instance: float


def estimate_capacity(
    concurrent_users: int,
    output_tokens_per_request: int,
    think_time_s: float,
    tokens_per_s_per_instance: float,
    target_utilization: float = 0.65,
    min_replicas_ha: int = 2,
) -> CapacityPlan:
    """Estima instancias necesarias.

    Modelo (cola abierta simplificada):
      tiempo_servicio = tokens_salida / tps_instancia
      ciclo_usuario   = tiempo_pensado + tiempo_servicio
      λ (req/s)       = usuarios_concurrentes / ciclo_usuario
      carga (tok/s)   = λ * tokens_salida
      instancias      = ceil(carga / (tps_instancia * utilización_objetivo))
    Para alta disponibilidad se exige al menos `min_replicas_ha` réplicas y
    N+1 (una de reserva) sobre las necesarias por carga.
    """
    if concurrent_users <= 0 or output_tokens_per_request <= 0:
        raise ValueError("Usuarios y tokens de salida deben ser positivos.")
    if not 0 < target_utilization <= 1:
        raise ValueError("La utilización objetivo debe estar en (0, 1].")
    if tokens_per_s_per_instance <= 0 or think_time_s < 0:
        raise ValueError("Parámetros inválidos.")
    service_s = output_tokens_per_request / tokens_per_s_per_instance
    lam = concurrent_users / (think_time_s + service_s)
    needed = lam * output_tokens_per_request
    effective = tokens_per_s_per_instance * target_utilization
    n_load = max(1, math.ceil(needed / effective))
    n_ha = max(min_replicas_ha, n_load + 1)
    return CapacityPlan(lam, needed, n_load, n_ha, effective)


# ---------------------------------------------------------------------------
# 2. Estrategias de compra (on-demand / compromiso / spot)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StrategyCost:
    name: str
    monthly_usd: float
    detail: str


def compare_purchase_strategies(
    catalog: Catalog,
    instance: Instance,
    baseline_instances: int,
    peak_extra_instances: int,
    peak_hours_per_month: float,
    commitment: str = "1y",
) -> list[StrategyCost]:
    """Compara 4 estrategias para una flota con base estable + picos.

    * all_on_demand:   todo a precio de lista.
    * commit_baseline: la base estable con compromiso, los picos on-demand.
    * commit_spot:     base con compromiso y picos en spot (con sobrecosto por
                       reintentos/interrupciones). Solo válido si el pico
                       tolera interrupciones (p. ej., trabajo batch).
    * all_commit_peak: error clásico: comprometer también el pico -> se paga
                       24x7 capacidad que solo se usa pocas horas.
    """
    if baseline_instances < 0 or peak_extra_instances < 0:
        raise ValueError("Número de instancias inválido.")
    if not 0 <= peak_hours_per_month <= catalog.hours_per_month:
        raise ValueError("Las horas de pico deben estar entre 0 y las horas del mes.")
    if commitment not in catalog.commitment_discount:
        raise ValueError(f"Compromiso '{commitment}' no definido en el catálogo.")

    h = catalog.hours_per_month
    od = instance.hourly_on_demand
    committed = od * (1 - catalog.commitment_discount[commitment])
    spot = od * (1 - catalog.spot_discount) * (1 + catalog.spot_overhead)

    all_od = baseline_instances * od * h + peak_extra_instances * od * peak_hours_per_month
    commit_base = baseline_instances * committed * h + peak_extra_instances * od * peak_hours_per_month
    commit_spot = baseline_instances * committed * h + peak_extra_instances * spot * peak_hours_per_month
    all_commit = (baseline_instances + peak_extra_instances) * committed * h

    return [
        StrategyCost("all_on_demand", all_od, "Todo a precio de lista"),
        StrategyCost("commit_baseline", commit_base, f"Base con compromiso {commitment}, picos on-demand"),
        StrategyCost("commit_spot", commit_spot, f"Base {commitment}, picos en spot (tolera interrupciones)"),
        StrategyCost("all_commit_peak", all_commit, "Compromiso también sobre el pico (riesgo de capacidad ociosa)"),
    ]


# ---------------------------------------------------------------------------
# 3. Punto de equilibrio: API administrada vs autogestionado
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BreakEven:
    api_cost_per_request_usd: float
    selfhosted_monthly_usd: float
    breakeven_requests_per_month: float
    selfhosted_cost_per_mtok_out_at_util_usd: float


def break_even_api_vs_selfhosted(
    catalog: Catalog,
    instance: Instance,
    replicas: int,
    input_tokens: int,
    output_tokens: int,
    utilization: float,
) -> BreakEven:
    if replicas <= 0 or input_tokens < 0 or output_tokens <= 0:
        raise ValueError("Parámetros inválidos.")
    if not 0 < utilization <= 1:
        raise ValueError("Utilización debe estar en (0, 1].")
    api_req = (input_tokens * catalog.api_in_per_mtok + output_tokens * catalog.api_out_per_mtok) / 1e6
    monthly = replicas * instance.hourly_on_demand * catalog.hours_per_month
    be = monthly / api_req if api_req > 0 else math.inf
    cost_mtok_out = instance.hourly_on_demand / (instance.tokens_per_s * 3600 * utilization) * 1e6
    return BreakEven(api_req, monthly, be, cost_mtok_out)


# ---------------------------------------------------------------------------
# 4. Rightsizing
# ---------------------------------------------------------------------------


def percentile(values: list[float], pct: float) -> float:
    if not values:
        raise ValueError("Serie vacía.")
    s = sorted(values)
    k = (len(s) - 1) * pct / 100.0
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def read_utilization_csv(path: Path | str) -> list[float]:
    with open(path, newline="", encoding="utf-8") as f:
        return [float(r["utilizacion_pct"]) for r in csv.DictReader(f)]


@dataclass(frozen=True)
class RightsizeAdvice:
    current: str
    p50: float
    p95: float
    recommended: str
    monthly_current_usd: float
    monthly_recommended_usd: float
    monthly_saving_usd: float
    note: str


def recommend_rightsizing(
    catalog: Catalog,
    current_name: str,
    utilization_pct: list[float],
    replicas: int = 1,
    target_util_pct: float = 70.0,
) -> RightsizeAdvice:
    """Elige la instancia más barata cuya capacidad cubra el p95 con holgura.

    Se usa p95 (no el promedio): el promedio oculta los picos y provoca
    degradación; el máximo sobredimensiona por un evento aislado.
    """
    cur = catalog.instance(current_name)
    p50, p95 = percentile(utilization_pct, 50), percentile(utilization_pct, 95)
    needed_capacity = cur.relative_capacity * (p95 / target_util_pct)
    candidates = sorted(catalog.instances.values(), key=lambda i: i.hourly_on_demand)
    rec = next((i for i in candidates if i.relative_capacity >= needed_capacity), candidates[-1])
    if rec.hourly_on_demand >= cur.hourly_on_demand:
        rec = cur
    h = catalog.hours_per_month
    cur_cost = replicas * cur.hourly_on_demand * h
    rec_cost = replicas * rec.hourly_on_demand * h
    if rec.name == cur.name:
        note = "Sin cambio: el tamaño actual es el adecuado para el p95 observado."
    else:
        note = (
            f"Reducir de {cur.name} a {rec.name}: el p95 ({p95:.0f} %) cabe con holgura. "
            "Validar con prueba de carga antes de aplicar."
        )
    return RightsizeAdvice(cur.name, p50, p95, rec.name, cur_cost, rec_cost, cur_cost - rec_cost, note)
