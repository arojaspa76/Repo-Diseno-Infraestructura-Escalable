"""CLI del simulador FinOps.

Ejemplos:
  python -m finops_sim catalog
  python -m finops_sim capacity --instance gpu-s --users 100 --out-tokens 300 --think 30
  python -m finops_sim strategies --instance gpu-s --baseline 2 --peak-extra 2 --peak-hours 120
  python -m finops_sim breakeven --instance gpu-s --replicas 2 --in-tokens 800 --out-tokens 300 --util 0.4
  python -m finops_sim rightsize --instance gpu-m --csv data/utilizacion_ejemplo.csv
  python -m finops_sim scenario --instance gpu-s            # caso universidad completo
"""

from __future__ import annotations

import argparse
import sys

from .calc import (
    break_even_api_vs_selfhosted,
    compare_purchase_strategies,
    estimate_capacity,
    read_utilization_csv,
    recommend_rightsizing,
)
from .catalog import Catalog, load_catalog


def _usd(x: float) -> str:
    return f"${x:,.2f}"


def _banner(cat: Catalog) -> None:
    print(f"\n[AVISO] {cat.notice}\n" if cat.notice else "")


def cmd_catalog(cat: Catalog, _: argparse.Namespace) -> int:
    _banner(cat)
    print(f"{'instancia':<8} {'USD/h':>7} {'tok/s':>7}  descripción")
    for i in cat.instances.values():
        print(f"{i.name:<8} {i.hourly_on_demand:>7.2f} {i.tokens_per_s:>7.0f}  {i.description}")
    return 0


def cmd_capacity(cat: Catalog, a: argparse.Namespace) -> int:
    inst = cat.instance(a.instance)
    tps = a.tps or inst.tokens_per_s
    plan = estimate_capacity(a.users, a.out_tokens, a.think, tps, a.util)
    _banner(cat)
    print(f"Instancia: {inst.name} ({tps:.0f} tok/s asumidos; use el valor medido en lab06)")
    print(f"Solicitudes/s estimadas : {plan.requests_per_s:.2f}")
    print(f"Carga de generación     : {plan.needed_tokens_per_s:.0f} tok/s")
    print(f"Capacidad útil/instancia: {plan.effective_tokens_per_s_per_instance:.0f} tok/s (a {a.util:.0%} de utilización objetivo)")
    print(f"Instancias por carga    : {plan.instances_for_load}")
    print(f"Instancias con HA (N+1) : {plan.instances_with_ha}")
    return 0


def cmd_strategies(cat: Catalog, a: argparse.Namespace) -> int:
    inst = cat.instance(a.instance)
    rows = compare_purchase_strategies(
        cat, inst, a.baseline, a.peak_extra, a.peak_hours, a.commitment
    )
    _banner(cat)
    base = rows[0].monthly_usd
    print(f"{'estrategia':<18} {'USD/mes':>12} {'vs on-demand':>14}  detalle")
    for r in rows:
        delta = (r.monthly_usd / base - 1) * 100 if base else 0.0
        print(f"{r.name:<18} {_usd(r.monthly_usd):>12} {delta:>13.1f}%  {r.detail}")
    return 0


def cmd_breakeven(cat: Catalog, a: argparse.Namespace) -> int:
    inst = cat.instance(a.instance)
    be = break_even_api_vs_selfhosted(cat, inst, a.replicas, a.in_tokens, a.out_tokens, a.util)
    _banner(cat)
    print(f"Costo por solicitud (API)         : ${be.api_cost_per_request_usd:.6f}")
    print(f"Autogestionado ({a.replicas}x {inst.name}) / mes : {_usd(be.selfhosted_monthly_usd)}")
    print(f"Punto de equilibrio               : {be.breakeven_requests_per_month:,.0f} solicitudes/mes")
    print(f"Costo autogestionado / 1M tok sal.: {_usd(be.selfhosted_cost_per_mtok_out_at_util_usd)} (a {a.util:.0%} de utilización)")
    print(f"Costo API / 1M tok salida         : {_usd(cat.api_out_per_mtok)}")
    return 0


def cmd_rightsize(cat: Catalog, a: argparse.Namespace) -> int:
    series = read_utilization_csv(a.csv)
    adv = recommend_rightsizing(cat, a.instance, series, a.replicas, a.target)
    _banner(cat)
    print(f"Muestras: {len(series)} | p50 = {adv.p50:.1f} % | p95 = {adv.p95:.1f} %")
    print(f"Actual: {adv.current} ({_usd(adv.monthly_current_usd)}/mes)")
    print(f"Recomendada: {adv.recommended} ({_usd(adv.monthly_recommended_usd)}/mes)")
    print(f"Ahorro mensual: {_usd(adv.monthly_saving_usd)}")
    print(adv.note)
    return 0


def cmd_scenario(cat: Catalog, a: argparse.Namespace) -> int:
    """Caso transversal: asistente institucional (5.000 usuarios, 100 concurrentes, 99,9 %)."""
    inst = cat.instance(a.instance)
    plan = estimate_capacity(100, a.out_tokens, a.think, a.tps or inst.tokens_per_s)
    n = plan.instances_with_ha
    _banner(cat)
    print("== Caso: asistente institucional de conocimiento ==")
    print("Supuestos: 5.000 usuarios, 100 concurrentes, disponibilidad objetivo 99,9 %")
    print(f"Instancia {inst.name}: {plan.instances_for_load} por carga -> {n} con HA (N+1)\n")
    # Base: las réplicas mínimas de HA siempre; pico: el resto durante horas de clase.
    base = min(2, n)
    peak_extra = max(0, n - base)
    rows = compare_purchase_strategies(cat, inst, base, peak_extra, a.peak_hours, a.commitment)
    print(f"Flota: base={base} siempre activa + {peak_extra} extra en {a.peak_hours:.0f} h/mes de pico")
    base_cost = rows[0].monthly_usd
    for r in rows:
        print(f"  {r.name:<18} {_usd(r.monthly_usd):>12}  ({(r.monthly_usd / base_cost - 1) * 100:+.1f} % vs on-demand)")
    monthly_requests = 5000 * a.requests_per_user_month
    api = (monthly_requests * (a.in_tokens * cat.api_in_per_mtok + a.out_tokens * cat.api_out_per_mtok)) / 1e6
    print(f"\nAlternativa API administrada: {monthly_requests:,} solicitudes/mes -> {_usd(api)}/mes")
    best = min(rows[:3], key=lambda r: r.monthly_usd)
    print(f"Mejor autogestionada ({best.name}): {_usd(best.monthly_usd)}/mes")
    print("Lectura: compare ambos números junto con costo operativo (personal, seguridad, soporte).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="finops_sim", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--catalog", help="Ruta a un catálogo JSON propio (por defecto, el ilustrativo).")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("catalog", help="Muestra el catálogo de supuestos.")

    c = sub.add_parser("capacity", help="Estima instancias necesarias.")
    c.add_argument("--instance", required=True)
    c.add_argument("--users", type=int, default=100)
    c.add_argument("--out-tokens", type=int, default=300)
    c.add_argument("--think", type=float, default=30.0, help="Segundos entre solicitudes de un usuario.")
    c.add_argument("--tps", type=float, help="tokens/s medidos (sobrescribe el catálogo).")
    c.add_argument("--util", type=float, default=0.65)

    s = sub.add_parser("strategies", help="Compara on-demand / compromiso / spot.")
    s.add_argument("--instance", required=True)
    s.add_argument("--baseline", type=int, required=True)
    s.add_argument("--peak-extra", type=int, required=True)
    s.add_argument("--peak-hours", type=float, required=True)
    s.add_argument("--commitment", default="1y")

    b = sub.add_parser("breakeven", help="API administrada vs autogestionado.")
    b.add_argument("--instance", required=True)
    b.add_argument("--replicas", type=int, default=2)
    b.add_argument("--in-tokens", type=int, default=800)
    b.add_argument("--out-tokens", type=int, default=300)
    b.add_argument("--util", type=float, default=0.4)

    r = sub.add_parser("rightsize", help="Recomienda tamaño según utilización.")
    r.add_argument("--instance", required=True)
    r.add_argument("--csv", required=True)
    r.add_argument("--replicas", type=int, default=1)
    r.add_argument("--target", type=float, default=70.0)

    sc = sub.add_parser("scenario", help="Caso transversal de la universidad.")
    sc.add_argument("--instance", required=True)
    sc.add_argument("--in-tokens", type=int, default=800)
    sc.add_argument("--out-tokens", type=int, default=300)
    sc.add_argument("--think", type=float, default=30.0)
    sc.add_argument("--tps", type=float)
    sc.add_argument("--peak-hours", type=float, default=120.0)
    sc.add_argument("--commitment", default="1y")
    sc.add_argument("--requests-per-user-month", type=int, default=40)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cat = load_catalog(args.catalog)
        handler = {
            "catalog": cmd_catalog,
            "capacity": cmd_capacity,
            "strategies": cmd_strategies,
            "breakeven": cmd_breakeven,
            "rightsize": cmd_rightsize,
            "scenario": cmd_scenario,
        }[args.cmd]
        return handler(cat, args)
    except (ValueError, OSError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
