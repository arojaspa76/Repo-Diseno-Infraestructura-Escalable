#!/usr/bin/env bash
# Copia la fuente única de las herramientas a cada ejemplo (cada carpeta debe poder desplegarse sola).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/cloud_agents/shared/capacity_tools.py"
for dest in \
  cloud_agents/gcp/adk_agent/capacity_advisor \
  cloud_agents/azure/agent_framework \
  cloud_agents/azure/semantic_kernel \
  cloud_agents/azure/autogen \
  cloud_agents/azure/langgraph \
  cloud_agents/aws/strands_agentcore; do
  mkdir -p "$ROOT/$dest"
  cp "$SRC" "$ROOT/$dest/capacity_tools.py"
  echo "sincronizado → $dest"
done
