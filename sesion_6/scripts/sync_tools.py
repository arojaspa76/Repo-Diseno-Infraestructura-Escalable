#!/usr/bin/env python3
"""Copia cloud-agents/common/finops_tools.py a cada ejemplo (copias vendorizadas).

Uso:
  python scripts/sync_tools.py          # copia
  python scripts/sync_tools.py --check  # falla (exit 1) si alguna copia difiere
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "cloud-agents" / "common" / "finops_tools.py"
HEADER = (
    "# ARCHIVO COPIADO AUTOMÁTICAMENTE desde cloud-agents/common/finops_tools.py\n"
    "# por scripts/sync_tools.py. NO EDITAR AQUÍ: edite el original y vuelva a sincronizar.\n"
)
TARGETS = [
    "cloud-agents/gcp/adk_agent/finops_agent",
    "cloud-agents/azure/maf",
    "cloud-agents/azure/semantic_kernel",
    "cloud-agents/azure/autogen_legacy",
    "cloud-agents/azure/langgraph_agent",
    "cloud-agents/aws/strands_agentcore",
]


def expected() -> str:
    return HEADER + SOURCE.read_text(encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    want = expected()
    bad = 0
    for rel in TARGETS:
        dest = ROOT / rel / "finops_tools.py"
        if args.check:
            if not dest.exists() or dest.read_text(encoding="utf-8") != want:
                print(f"DESINCRONIZADO: {rel}/finops_tools.py")
                bad += 1
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(want, encoding="utf-8")
            print(f"copiado -> {rel}/finops_tools.py")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
