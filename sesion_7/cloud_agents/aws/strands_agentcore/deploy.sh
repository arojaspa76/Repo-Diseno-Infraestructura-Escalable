#!/usr/bin/env bash
# Despliega el agente en Amazon Bedrock AgentCore Runtime con el starter toolkit (flujo documentado por AWS).
# ⚠ Genera costos. Al terminar ejecute la LIMPIEZA descrita en cloud_agents/aws/README.md.
set -euo pipefail
cd "$(dirname "$0")"
REGION="${AWS_REGION:-us-east-1}"

command -v agentcore >/dev/null || { echo "Instale las dependencias: pip install -r requirements.txt"; exit 1; }

agentcore configure -e agent.py -r "$REGION"   # asistente interactivo (rol IAM, ECR, etc.)
agentcore launch                               # construye el contenedor y despliega el runtime
agentcore invoke '{"prompt": "¿Cabe Llama 3.1 8B en FP16 en una GPU de 24 GB con 8 conversaciones de 8192 tokens?"}'

# Nota: versiones recientes de la documentación también muestran un CLI nuevo (`agentcore create` / `agentcore deploy`).
# Si su versión es distinta, siga `agentcore --help` y la guía oficial enlazada en el README.
