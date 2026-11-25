#!/usr/bin/env bash
# Despliega el agente en Vertex AI Agent Engine (hoy documentado como parte de "Gemini Enterprise Agent Platform").
# ⚠ Genera costos. Revise docs/05_costos_finops.md y ejecute la LIMPIEZA al terminar (README de esta carpeta).
set -euo pipefail
: "${PROJECT_ID:?Defina PROJECT_ID}"
LOCATION_ID="${LOCATION_ID:-us-central1}"
cd "$(dirname "$0")"

gcloud config set project "$PROJECT_ID"
gcloud services enable aiplatform.googleapis.com

# Los flags del comando pueden cambiar entre versiones de ADK: confirme con `adk deploy agent_engine --help`.
adk deploy agent_engine --project="$PROJECT_ID" --region="$LOCATION_ID" capacity_advisor
