#!/usr/bin/env bash
# Configura el servicio systemd de Ollama para atender varias peticiones en paralelo y mantener el modelo en memoria.
#   NUM_PARALLEL  peticiones simultáneas por modelo (más = más KV cache en memoria)
#   KEEP_ALIVE    cuánto tiempo permanece cargado el modelo tras la última petición
# Uso:  sudo bash configure_parallel.sh 4 10m
set -euo pipefail
PAR="${1:-4}"; KEEP="${2:-10m}"
[ "$(id -u)" -eq 0 ] || { echo "Ejecute con sudo"; exit 1; }
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf <<CONF
[Service]
Environment="OLLAMA_NUM_PARALLEL=${PAR}"
Environment="OLLAMA_KEEP_ALIVE=${KEEP}"
CONF
systemctl daemon-reload
systemctl restart ollama
echo "Ollama reiniciado con OLLAMA_NUM_PARALLEL=${PAR} y OLLAMA_KEEP_ALIVE=${KEEP}"
