.PHONY: setup test backend frontend up down lint sync-tools
PY ?= python3.12

setup:            ## Crea el entorno virtual e instala dependencias
	$(PY) -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements-dev.txt
	cd app/frontend && npm install

test:             ## Pruebas del backend y de las herramientas compartidas de los agentes
	. .venv/bin/activate && cd app/backend && python -m pytest -q
	. .venv/bin/activate && python -m pytest -q cloud_agents/tests

backend:          ## Backend en http://localhost:8000 (docs en /docs)
	. .venv/bin/activate && cd app/backend && uvicorn app.main:app --reload --port 8000

frontend:         ## Frontend en http://localhost:5173
	cd app/frontend && npm run dev

up:               ## Pila completa con Docker (solo CPU)
	cd app && docker compose up --build

down:
	cd app && docker compose down

sync-tools:       ## Copia cloud_agents/shared/capacity_tools.py a cada ejemplo de agente
	bash scripts/sync_tools.sh
