#!/usr/bin/env bash
# Instala Ollama (Linux) y descarga los modelos del laboratorio.
# Lee el script de instalación ANTES de ejecutarlo si desea revisar qué hace: https://ollama.com/install.sh
set -euo pipefail

if ! command -v ollama >/dev/null; then
  echo "→ Instalando Ollama…"
  curl -fsSL https://ollama.com/install.sh | sh
fi
ollama --version

MODELS=("llama3.2:1b" "nomic-embed-text")
for m in "${MODELS[@]}"; do
  echo "→ Descargando $m …"
  ollama pull "$m"
done
echo "Listo. Pruebe:  ollama run llama3.2:1b \"Hola\""
