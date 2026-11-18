"""Carga y validación del catálogo de supuestos de precio."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CATALOG = Path(__file__).resolve().parent.parent / "data" / "catalogo_ilustrativo.json"


@dataclass(frozen=True)
class Instance:
    name: str
    description: str
    hourly_on_demand: float
    relative_capacity: float
    tokens_per_s: float


@dataclass(frozen=True)
class Catalog:
    hours_per_month: float
    instances: dict[str, Instance]
    commitment_discount: dict[str, float]  # "1y" -> 0.30
    spot_discount: float
    spot_overhead: float
    api_in_per_mtok: float
    api_out_per_mtok: float
    notice: str

    def instance(self, name: str) -> Instance:
        try:
            return self.instances[name]
        except KeyError as exc:
            raise ValueError(
                f"Instancia '{name}' no existe. Opciones: {', '.join(self.instances)}"
            ) from exc


def _check_fraction(label: str, value: float) -> float:
    if not 0.0 <= value < 1.0:
        raise ValueError(f"{label} debe estar en [0, 1): {value}")
    return value


def load_catalog(path: Path | str | None = None) -> Catalog:
    data = json.loads(Path(path or DEFAULT_CATALOG).read_text(encoding="utf-8"))
    instances = {
        name: Instance(
            name=name,
            description=v["descripcion"],
            hourly_on_demand=float(v["precio_hora_on_demand"]),
            relative_capacity=float(v["capacidad_relativa"]),
            tokens_per_s=float(v["tokens_por_segundo"]),
        )
        for name, v in data["instancias"].items()
    }
    for inst in instances.values():
        if inst.hourly_on_demand <= 0 or inst.tokens_per_s <= 0:
            raise ValueError(f"Valores inválidos en instancia {inst.name}")
    return Catalog(
        hours_per_month=float(data.get("horas_por_mes", 730)),
        instances=instances,
        commitment_discount={
            k: _check_fraction(f"compromiso {k}", float(v["descuento"]))
            for k, v in data["compromiso"].items()
        },
        spot_discount=_check_fraction("spot.descuento", float(data["spot"]["descuento"])),
        spot_overhead=float(data["spot"]["sobrecosto_por_interrupciones"]),
        api_in_per_mtok=float(data["api_administrada"]["precio_entrada_por_mtok"]),
        api_out_per_mtok=float(data["api_administrada"]["precio_salida_por_mtok"]),
        notice=data.get("_aviso", ""),
    )
