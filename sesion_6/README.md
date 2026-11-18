# Sesión 6 · FinOps y optimización de costos para LLMs en la nube

Material del curso **Diseño de Infraestructura Escalable para LLMs** (Capítulo 3, Sesión 6, 3 horas).

## ¿De qué trata?

Poner un asistente con IA en producción cuesta dinero cada vez que alguien le hace una pregunta, y cuesta aún más si los servidores están encendidos sin usarse. Esta sesión enseña a **decidir cómo pagar** (por uso, con compromiso o con capacidad sobrante más barata), **cuánto hardware pedir**, **cómo vigilar el gasto** y **cómo protegerse** de usos abusivos y ataques propios de los modelos de lenguaje.

El caso que usamos en todo el repositorio: *un asistente de conocimiento para una universidad* (5.000 usuarios, 100 conectados a la vez, disponible el 99,9 % del tiempo).

## ¿Qué hay en este repositorio?

| Carpeta | Qué contiene | Para quién |
|---------|--------------|------------|
| `docs/` | Teoría, arquitecturas, seguridad, guía del estudiante y **mapa de ejemplos** | Todos: empiece por `docs/00-mapa-ejemplos.md` |
| `labs/` | Siete laboratorios paso a paso (qué hacer, qué debe ver, cuánto cuesta, cómo limpiar) | Estudiantes |
| `backend/` | Un «portero» (gateway) en FastAPI que se coloca delante del modelo: autentica, limita, mide costos y filtra | Laboratorios 1, 2, 5, 7 |
| `frontend/` | Tablero web (React) para ver consumo y presupuesto | Laboratorio 2 |
| `finops/` | Simulador de costos por consola (precios **ilustrativos**) | Laboratorios 3 y 4 |
| `loadtest/` | Generador de carga para medir latencia y disponibilidad | Laboratorio 6 |
| `cloud-agents/` | Un mismo agente FinOps construido en Google, Azure y AWS, por consola y por código | Demostraciones |

## Inicio rápido (sin nube, sin costo)

Requisitos: Ubuntu 24.04 o superior (o WSL2), Python 3.12, Node 22.

```bash
make setup          # crea .venv e instala dependencias
make test           # ejecuta todas las pruebas automáticas
make finops-demo    # ejecuta el simulador del caso universitario
```

Para conversar con un modelo local (opcional), siga `labs/lab1-ollama/README.md`.
Con Docker: `docker compose up -d --build` (ver aviso en el laboratorio 2: esta vía **no se ha probado** en el entorno de preparación).

## Avisos importantes

- **Los precios del repositorio son ilustrativos.** No son tarifas reales de ningún proveedor. Use las calculadoras oficiales (enlaces en `docs/04-finops-llm.md`).
- **Los ejemplos en la nube no se ejecutaron contra servicios reales** al prepararlos; se comprobó que el código se construye con los SDK instalados. Cada carpeta indica qué falta.
- Nunca suba archivos `.env`. Los ejemplos usan identidad (Entra ID, IAM/ADC), no claves en el código.
- Cada laboratorio en la nube indica su **costo posible** y su **limpieza**. Si usa cuenta de prueba, configure alertas de presupuesto antes de empezar.

## Licencias

Código: MIT (`LICENSE`). Materiales de enseñanza: CC BY-SA 4.0 (`docs/LICENCIA-MATERIALES.md`).
