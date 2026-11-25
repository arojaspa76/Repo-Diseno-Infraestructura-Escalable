# Sesión 7 · Optimización de latencia y throughput en LLMs

**Curso:** Diseño de Infraestructura Escalable para LLMs · **Capítulo 4:** Optimización de rendimiento y alta disponibilidad · **Duración:** 3 horas

---

## 1. ¿De qué trata esta sesión? (en lenguaje sencillo)

Un modelo de lenguaje (LLM) puede dar respuestas excelentes y, aun así, ser **inutilizable** si tarda 20 segundos en empezar a contestar,
o **imposible de pagar** si cada usuario necesita una GPU entera. Esta sesión enseña a **medir** y **mejorar** tres cosas:

| Pregunta del usuario | Lo que medimos | Se mejora con… |
|---|---|---|
| "¿Cuándo empieza a responder?" | **Latencia** (TTFT, TPOT) | Streaming, cache, mantener el modelo cargado, prompts cortos |
| "¿Cuántas personas puede atender a la vez?" | **Throughput** y capacidad | Batching, KV cache bien dimensionado, más réplicas |
| "¿Cuánto cuesta?" | **Memoria y costo** | Cuantización, cache, modelo adecuado, FinOps |

Todo se aprende **midiendo** en su propio computador con un LLM real ejecutado localmente (Ollama), y luego se conecta con lo que ofrecen
**Azure, Google Cloud y AWS** para construir agentes.

## 2. ¿Qué voy a ser capaz de hacer al terminar?

1. Explicar con claridad qué ocurre dentro de una inferencia (prefill, decode, KV cache) y por qué importa para el diseño.
2. **Medir** TTFT, TPOT, throughput y percentiles (p50/p95/p99) de un servicio de LLM.
3. **Perfilar** CPU, RAM, GPU y red para encontrar el cuello de botella.
4. **Calcular** cuánta memoria de GPU necesita un modelo y cuántas conversaciones caben.
5. Aplicar **batching, reuso de prefijo, cuantización y cache de embeddings** y medir su efecto.
6. Identificar los riesgos de seguridad de una aplicación LLM (OWASP) y aplicar controles básicos.
7. Reconocer cómo crear un **agente sencillo** en Azure, Google Cloud y AWS, desde la consola y desde código.

## 3. ¿Cómo está organizada la sesión de 3 horas?

| Tiempo | Bloque | Tipo | Material del repositorio |
|---|---|---|---|
| 0:00 | Apertura y caso de estudio | Teoría | — |
| 0:05 | **B1** Anatomía de una inferencia y métricas | Teoría | `docs/02_conceptos_clave.md` |
| 0:25 | **B2** Profiling: GPU, CPU, RAM, red | Teoría | `labs/lab02_profiling/` |
| 0:45 | **Demo 1** Ollama + profiling + calculadora | Demo | `labs/lab01…`, `lab02…`, `E03b` |
| 1:00 | Descanso | — | — |
| 1:10 | **B3** Batching y KV cache | Teoría | `labs/lab03_batching_kvcache/` |
| 1:30 | **B4** Cuantización y cache de embeddings | Teoría | `labs/lab04…`, `lab05…` |
| 1:45 | **Demo 2** Concurrencia y aplicación completa | Demo | `labs/lab03…`, `app/` |
| 2:05 | **B5** Arquitecturas base, patrones multicloud y FinOps | Teoría | `docs/01…`, `03…`, `05…` |
| 2:25 | **B6** Seguridad de aplicaciones LLM | Teoría | `docs/04_seguridad_llm.md` |
| 2:40 | **Demo 3** Agentes en la nube (consola y código) | Demo | `cloud_agents/` |
| 2:50 | Discusión y cierre | Discusión | `docs/07_guia_estudiante.md` |

Proporción: ≈ 64 % teoría · 25 % demostraciones · 11 % discusión y descanso.

## 4. Empiece aquí (3 caminos según su situación)

### Camino A — "Quiero ver todo funcionando" (≈ 30 min, Ubuntu 24.04 o WSL2)
```bash
git clone https://github.com/arojaspa76/Repo-Diseno-Infraestructura-Escalable.git
cd Repo-Diseno-Infraestructura-Escalable/sesion_07
make setup                                         # entorno Python 3.12 + dependencias + npm install
bash labs/lab01_ollama_local/install_and_pull.sh   # Ollama + modelos
make backend                                       # terminal 1  → http://localhost:8000/docs
make frontend                                      # terminal 2  → http://localhost:5173
```
Guía detallada con explicaciones: [`docs/00_guia_instalacion_ubuntu.md`](docs/00_guia_instalacion_ubuntu.md).

### Camino B — "Prefiero Docker" (≈ 15 min)
```bash
cd sesion_07/app && docker compose up --build
docker compose exec ollama ollama pull llama3.2:1b && docker compose exec ollama ollama pull nomic-embed-text
# Abra http://localhost:8080
```

### Camino C — "Mi computador no puede ejecutar modelos"
Use el servidor **simulado** (los números son sintéticos; sirve para ver que el código funciona):
```bash
python scripts/fake_ollama.py --port 11435 &
export OLLAMA_BASE_URL=http://127.0.0.1:11435
python labs/lab03_batching_kvcache/batching_simulator.py          # este no necesita ningún servidor
```

## 5. ¿Qué hay en cada carpeta?

| Carpeta / archivo | En una frase | Cuándo lo usará |
|---|---|---|
| [`docs/`](docs/) | Explicaciones teóricas, arquitectura, seguridad, costos, referencias y ADR | **Antes** de clase (lea `02_conceptos_clave.md`) |
| [`labs/`](labs/) | Seis laboratorios guiados con scripts de Python y su README | Durante y después de clase |
| [`app/`](app/) | Aplicación completa: backend FastAPI + frontend React 18/Vite 6 + Docker | Demo 2 y como plantilla de proyecto |
| [`cloud_agents/`](cloud_agents/) | El mismo agente creado en Azure, Google Cloud y AWS (consola + código) | Demo 3 y su tarea de nube |
| [`loadtest/`](loadtest/) | Prueba de carga con Locust | Cuando quiera estresar el backend |
| [`scripts/`](scripts/) | Utilidades (servidor simulado, sincronización de herramientas) | Casos puntuales |
| [`results/`](results/) | Aquí se guardan SUS mediciones (no se suben a Git) | Para su informe |
| [`MAPA_EJEMPLOS.md`](MAPA_EJEMPLOS.md) | **Tabla que une cada ejemplo de la presentación con su ruta y comando** | Siempre que la presentación nombre un ejemplo |

### Cómo leer las etiquetas de la presentación
Cuando una diapositiva diga **E03a** o **A2**, busque esa etiqueta en [`MAPA_EJEMPLOS.md`](MAPA_EJEMPLOS.md): le dirá la carpeta exacta y el comando para ejecutarlo.

## 6. Requisitos

| Elemento | Versión / mínimo | Nota |
|---|---|---|
| Sistema operativo | Ubuntu 24.04 LTS o superior (o WSL2) | |
| Python | 3.12 | |
| Node.js | 22 (npm incluido) | Solo para la interfaz web |
| Frontend | React 18 · Vite 6 · TypeScript | Se instala con `npm install` |
| Backend | FastAPI · Pydantic v2 | Se instala con `pip install -r requirements.txt` |
| Ollama | Última versión estable | Laboratorios 1–5 |
| RAM | 8 GB mínimo (16 GB recomendado) | Con modelos de 1B–3B parámetros |
| GPU | Opcional (NVIDIA) | Todo funciona en CPU, solo más lento |
| Docker | Opcional | Camino B |
| PostgreSQL | **No se usa** en esta sesión | |
| Cuentas cloud | *Trial* de Azure, Google Cloud y AWS | Solo para `cloud_agents/` |

## 7. Estado de verificación (transparencia)

| Componente | Estado | Cómo se comprobó |
|---|---|---|
| Backend FastAPI (21 pruebas) | ✅ Verificado | `pytest` con backend falso, Python 3.12 |
| Frontend React 18 + Vite 6 | ✅ Compila | `tsc --noEmit` + `vite build` |
| Scripts de laboratorio 1–6 | ✅ Ejecutan de punta a punta | Contra el **servidor simulado** |
| Herramientas de agentes | ✅ Probadas | `pytest` |
| Ejemplos de agentes (6) | ✅ Importan y construyen el agente con los SDK actuales | Sin llamar a la nube |
| Rendimiento con **Ollama real** (cifras) | ⏳ **Pendiente** | Requiere su hardware: este repositorio **no trae resultados de ejemplo** |
| Ejemplos **contra Azure / GCP / AWS reales** | ⏳ **Pendiente** | Requiere cuentas y credenciales |
| Docker compose | ⏳ Pendiente de ejecutar | Los Dockerfile no se construyeron durante la preparación |
| Pasos de consola | ℹ️ Según documentación oficial | Las interfaces cambian con frecuencia |

## 8. Seguridad y costos en una línea
Nunca suba claves al repositorio (`.env` está en `.gitignore`); use identidades (az login, SSO, ADC). Los laboratorios de nube pueden generar costos:
use cuentas *trial*, cree alertas de presupuesto y haga la **limpieza** indicada en cada README.

## 9. Preguntas frecuentes
**¿Los números del Lab 3 de mi compañero deben coincidir con los míos?** No. Dependen de CPU/GPU, memoria y versión de Ollama. Por eso se documenta el entorno en cada resultado.
**¿Por qué Ollama y no vLLM?** Por reproducibilidad en computadores de estudiantes (ver [ADR-001](docs/adr/ADR-001-ollama-para-laboratorio.md)). vLLM se estudia en teoría.
**¿Los guardrails del repositorio son suficientes para producción?** No: son una primera capa didáctica (ver [ADR-003](docs/adr/ADR-003-guardrails-en-capas.md)).

## 10. Licencias
Código: **MIT** (`LICENSE`). Materiales de enseñanza (`docs/` y presentación): **CC BY-SA 4.0**.
