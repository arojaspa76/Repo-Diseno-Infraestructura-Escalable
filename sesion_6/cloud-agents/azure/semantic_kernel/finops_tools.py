# ARCHIVO COPIADO AUTOMÁTICAMENTE desde cloud-agents/common/finops_tools.py
# por scripts/sync_tools.py. NO EDITAR AQUÍ: edite el original y vuelva a sincronizar.
"""Herramientas FinOps compartidas por TODOS los agentes de la sesión.

Este archivo es la fuente canónica. `scripts/sync_tools.py` lo copia a cada
ejemplo para que cada carpeta sea desplegable por sí sola (p. ej. zip de
AgentCore o contenedor de Agent Engine). No edite las copias.

Diseño seguro de herramientas (OWASP LLM03/LLM06 en el mapeo de la sesión):
  * Son funciones puras: sin red, sin disco, sin secretos -> mínimo privilegio.
  * Validan sus argumentos: el modelo puede enviar valores absurdos.
  * Devuelven datos estructurados con los supuestos explícitos.
"""

from __future__ import annotations

INSTRUCTIONS = (
    "Eres un asesor FinOps para el equipo de plataforma de una universidad que "
    "opera un asistente institucional basado en LLM. Responde en español, breve y "
    "con números. Usa SIEMPRE las herramientas para cualquier cálculo de costos; "
    "no calcules de memoria. Indica los supuestos que usaste. Si faltan datos "
    "(precios, volumen), pídelos en lugar de inventarlos. Los precios que te dé el "
    "usuario son la única fuente de precios: no cites precios de proveedores."
)

HOURS_PER_MONTH = 730


def estimate_monthly_inference_cost(
    requests_per_month: int,
    avg_input_tokens: int,
    avg_output_tokens: int,
    price_input_per_mtok_usd: float,
    price_output_per_mtok_usd: float,
) -> dict:
    """Estima el costo mensual de una API de LLM administrada (pago por token).

    Args:
        requests_per_month: solicitudes por mes.
        avg_input_tokens: tokens de entrada promedio por solicitud (incluye contexto RAG).
        avg_output_tokens: tokens de salida promedio por solicitud.
        price_input_per_mtok_usd: USD por millón de tokens de entrada.
        price_output_per_mtok_usd: USD por millón de tokens de salida.
    """
    for name, value in {
        "requests_per_month": requests_per_month,
        "avg_input_tokens": avg_input_tokens,
        "avg_output_tokens": avg_output_tokens,
        "price_input_per_mtok_usd": price_input_per_mtok_usd,
        "price_output_per_mtok_usd": price_output_per_mtok_usd,
    }.items():
        if value < 0:
            raise ValueError(f"{name} no puede ser negativo")
    if requests_per_month > 10_000_000_000:
        raise ValueError("requests_per_month fuera de rango razonable")
    input_cost = requests_per_month * avg_input_tokens * price_input_per_mtok_usd / 1e6
    output_cost = requests_per_month * avg_output_tokens * price_output_per_mtok_usd / 1e6
    total = input_cost + output_cost
    return {
        "input_cost_usd": round(input_cost, 2),
        "output_cost_usd": round(output_cost, 2),
        "total_monthly_usd": round(total, 2),
        "cost_per_request_usd": round(total / requests_per_month, 6) if requests_per_month else 0.0,
        "assumptions": "Pago por token; sin descuentos por volumen ni caché de prompts.",
    }


def compare_compute_purchase_options(
    on_demand_hourly_usd: float,
    instances: int,
    commitment_discount: float,
    spot_discount: float,
    spot_overhead: float = 0.10,
) -> dict:
    """Compara el costo mensual de una flota always-on: on-demand vs compromiso vs spot.

    Args:
        on_demand_hourly_usd: precio por hora on-demand de UNA instancia.
        instances: número de instancias siempre activas.
        commitment_discount: fracción de descuento por compromiso (0.30 = 30 %).
        spot_discount: fracción de descuento de spot (0.65 = 65 %).
        spot_overhead: sobrecosto por interrupciones/reintentos (0.10 = 10 %).
    """
    if on_demand_hourly_usd <= 0 or instances <= 0:
        raise ValueError("precio e instancias deben ser positivos")
    for name, v in {"commitment_discount": commitment_discount, "spot_discount": spot_discount}.items():
        if not 0 <= v < 1:
            raise ValueError(f"{name} debe estar en [0, 1)")
    if spot_overhead < 0:
        raise ValueError("spot_overhead no puede ser negativo")
    base = on_demand_hourly_usd * instances * HOURS_PER_MONTH
    committed = base * (1 - commitment_discount)
    spot = base * (1 - spot_discount) * (1 + spot_overhead)
    return {
        "on_demand_monthly_usd": round(base, 2),
        "commitment_monthly_usd": round(committed, 2),
        "spot_monthly_usd": round(spot, 2),
        "commitment_saving_pct": round(commitment_discount * 100, 1),
        "spot_saving_pct": round((1 - spot / base) * 100, 1),
        "assumptions": (
            f"{HOURS_PER_MONTH} h/mes. Spot puede interrumpirse: solo para cargas "
            "tolerantes a fallos. El compromiso exige uso estable de la base."
        ),
    }


TOOLS = [estimate_monthly_inference_cost, compare_compute_purchase_options]
