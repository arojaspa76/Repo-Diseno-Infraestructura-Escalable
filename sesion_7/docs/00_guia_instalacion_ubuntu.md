# Guía de instalación en Ubuntu 24.04 (paso a paso)

> Esta guía asume **cero experiencia previa** con las herramientas. Si algo falla, vaya a la sección *Problemas comunes* al final.
> Funciona igual en WSL2 con Ubuntu 24.04 en Windows 11.

## Qué vamos a instalar y para qué

| Herramienta | Para qué sirve en la sesión | ¿Obligatoria? |
|---|---|---|
| **Python 3.12** | Ejecutar el backend FastAPI y los laboratorios | Sí |
| **Ollama** | Ejecutar un LLM en su propio computador | Sí (laboratorios 1–5) |
| **Node.js 22 + npm** | Ejecutar/compilar la interfaz React | Solo para la interfaz web |
| **Docker** | Levantar toda la pila con un comando | Opcional |
| Cuentas cloud (trial) | Ejemplos de agentes en Azure, GCP y AWS | Solo para la parte de agentes |

## 1. Actualizar el sistema y herramientas base

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl build-essential python3.12 python3.12-venv python3-pip
python3.12 --version      # debe decir Python 3.12.x
```

## 2. Clonar el repositorio

```bash
git clone https://github.com/arojaspa76/Repo-Diseno-Infraestructura-Escalable.git
cd Repo-Diseno-Infraestructura-Escalable/sesion_07
```

## 3. Crear el entorno virtual de Python

Un *entorno virtual* es una carpeta aislada donde se instalan las librerías de este proyecto sin afectar al resto del sistema.

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # el prompt mostrará (.venv)
pip install -U pip
pip install -r requirements-dev.txt
```

## 4. Instalar Ollama y descargar modelos

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama --version
ollama pull llama3.2:1b            # ≈ 1.3 GB — modelo pequeño, corre en CPU
ollama pull nomic-embed-text       # modelo de embeddings (para el Lab 5)
ollama run llama3.2:1b "Hola, ¿quién eres?"
```

Pruebe que la API responde:

```bash
curl http://localhost:11434/api/version
```

**¿Cuánta memoria necesito?** Con 8 GB de RAM puede usar modelos de 1B–3B parámetros. Con GPU NVIDIA, Ollama la usa automáticamente
si los controladores están instalados (`nvidia-smi` debe funcionar).

## 5. (Opcional) Node.js 22 para la interfaz React

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node --version && npm --version
cd app/frontend && npm install && cd ../..
```

## 6. (Opcional) Docker

Siga la guía oficial: <https://docs.docker.com/engine/install/ubuntu/>. Después:

```bash
sudo usermod -aG docker $USER      # cierre sesión y vuelva a entrar
docker run --rm hello-world
```

## 7. Verificar que todo funciona

```bash
source .venv/bin/activate
make test                          # debe terminar con todas las pruebas en verde
```

## Sin Ollama ni GPU: modo simulado

Si su computador no puede ejecutar modelos, use el servidor simulado para comprobar que los scripts corren:

```bash
python scripts/fake_ollama.py --port 11435 &
export OLLAMA_BASE_URL=http://127.0.0.1:11435
```

⚠ Los números del modo simulado son **sintéticos**: sirven para ver que el código funciona, nunca para sacar conclusiones de rendimiento.

## Problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `python3.12: command not found` | Ubuntu < 24.04 | Use `uv` (<https://docs.astral.sh/uv/>): `uv venv --python 3.12` |
| `ollama: command not found` tras instalar | Terminal abierta antes de instalar | Cierre y abra la terminal |
| `connection refused` en `localhost:11434` | El servicio no está corriendo | `sudo systemctl start ollama` o ejecute `ollama serve` |
| La respuesta tarda minutos | Modelo demasiado grande para su RAM/CPU | Use `llama3.2:1b` |
| `npm install` falla | Node muy antiguo | Instale Node 22 (paso 5) |
| WSL2: `nvidia-smi` no funciona | Falta el controlador NVIDIA para WSL | Instale el driver en **Windows** (no dentro de WSL) |
