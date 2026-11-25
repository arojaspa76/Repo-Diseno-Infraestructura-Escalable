#!/usr/bin/env bash
# Pruebas rápidas de que Ollama responde. No requiere herramientas extra (solo curl).
set -euo pipefail
BASE="${OLLAMA_BASE_URL:-http://localhost:11434}"
MODEL="${1:-llama3.2:1b}"

echo "1) Versión del servidor:"; curl -fsS "$BASE/api/version"; echo
echo "2) Modelos instalados:";    curl -fsS "$BASE/api/tags" | head -c 400; echo
echo "3) Chat sin streaming (mide el tiempo total con curl):"
curl -fsS -w "\n   → tiempo total: %{time_total}s\n" "$BASE/api/chat" -d "{
  \"model\": \"$MODEL\", \"stream\": false,
  \"messages\": [{\"role\":\"user\",\"content\":\"Responde con una sola frase: ¿qué es un LLM?\"}]
}" | head -c 600
echo
echo "4) Modelos cargados en memoria (¿en GPU o en RAM?):"; curl -fsS "$BASE/api/ps"; echo
