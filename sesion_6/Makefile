.PHONY: setup test test-backend test-finops test-loadtest test-tools test-frontend run-backend run-frontend up down pull-model finops-demo sync-tools
PY ?= python3.12
VENV ?= .venv

setup:                      ## Crea el entorno virtual e instala dependencias (backend + pruebas)
	$(PY) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	cd frontend && npm install --no-audit --no-fund

test: test-backend test-finops test-loadtest test-tools test-frontend   ## Toda la batería de pruebas

test-backend:
	cd backend && ../$(VENV)/bin/python -m pytest -q
test-finops:
	cd finops && ../$(VENV)/bin/python -m pytest -q
test-loadtest:
	cd loadtest && ../$(VENV)/bin/python -m pytest -q
test-tools:
	cd cloud-agents/common && ../../$(VENV)/bin/python -m pytest -q
	$(VENV)/bin/python scripts/sync_tools.py --check
test-frontend:
	cd frontend && npm test && npm run build

run-backend:                ## Gateway en http://localhost:8000 (requiere Ollama corriendo)
	cd backend && ../$(VENV)/bin/uvicorn app.main:build_default_app --factory --reload --port 8000
run-frontend:               ## Dashboard en http://localhost:5173
	cd frontend && npm run dev

up:                         ## Pila completa con Docker
	docker compose up -d --build
down:
	docker compose down
pull-model:                 ## Descarga el modelo dentro del contenedor de Ollama
	docker compose exec ollama ollama pull $${OLLAMA_MODEL:-llama3.2:1b}

finops-demo:                ## Caso de la universidad en el simulador FinOps
	cd finops && ../$(VENV)/bin/python -m finops_sim scenario --instance gpu-s
sync-tools:
	$(PY) scripts/sync_tools.py
