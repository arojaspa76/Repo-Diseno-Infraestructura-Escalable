# FinOps aplicado a LLM

## 1. Marco
**FinOps Framework (FinOps Foundation, edición 2025):** componentes: Principios, Scopes, Personas, Fases, Modelo de madurez, Dominios y Capacidades. Las **fases** (Inform, Optimize, Operate) son modos de trabajo que se repiten, no etapas de una sola vez. La edición 2025 añadió *Scopes* para extender FinOps más allá de la nube pública (incluye IA). Madurez: **Crawl → Walk → Run**. Los principios se resumen en: colaboración entre equipos, valor de negocio como motor de decisiones, responsabilidad (ownership) por el uso, datos accesibles y oportunos, y centralización del gobierno con ejecución descentralizada. **Verifique el texto vigente en finops.org** antes de citarlo literalmente.

## 2. Por qué el costo de LLM es distinto
- API administrada: pago por **token** (entrada y salida con tarifas distintas) → costo variable.
- Autogestionado: pago por **hora de GPU** → costo fijo mientras esté encendido; el **costo unitario depende de la utilización**.
- El costo crece con la longitud del contexto y de la salida, y con los reintentos de agentes.

## 3. Fórmulas usadas en el repositorio
- Costo API = (tokens_entrada × precio_entrada + tokens_salida × precio_salida) / 10⁶ por solicitud.
- Costo mensual de flota = instancias × horas × precio/hora (× (1 − descuento) donde aplique).
- Capacidad (modelo de cola abierta simplificado): tiempo de servicio = tokens_salida / tps; ciclo de usuario = tiempo_pensado + tiempo de servicio; λ = usuarios_concurrentes / ciclo; carga = λ × tokens_salida; instancias = ⌈carga / (tps × utilización_objetivo)⌉, y N+1 (mínimo 2 réplicas) para alta disponibilidad. Es un modelo didáctico: valide con prueba de carga.
- Punto de equilibrio = costo fijo mensual de la flota / costo por solicitud de la API.
- Rightsizing: elegir por **p95**, no por promedio, y validar con prueba de carga.

## 4. Modalidades de compra
| Modalidad | Idea | Riesgo | Equivalentes |
|---|---|---|---|
| On-demand | Pago por uso sin compromiso | Es lo más caro por hora | Todas |
| Compromiso | Descuento por comprometer uso 1–3 años | Pagar por capacidad no usada | AWS Reserved Instances / Savings Plans · Azure Reservations / Savings Plans · Google Committed Use Discounts |
| Spot / preemptible | Capacidad sobrante con gran descuento | Interrupción: avisos típicos de **2 min en AWS** y **~30 s en Azure y Google** (verifique en la documentación vigente) | EC2 Spot · Azure Spot VMs · Google Spot VMs |

Regla de oro: **comprometa la base estable, no el pico**; use spot solo para trabajo tolerante a interrupciones (lotes, evaluaciones, colas), no para el camino sincrónico del 99,9 %.

## 5. Presupuestos y alertas
| Nube | Herramienta | ¿Detiene el gasto? |
|---|---|---|
| Azure | Cost Management → Budgets (alertas reales y de pronóstico, *action groups*) | **No**, solo notifica; puede disparar automatización (Functions, Logic Apps, runbooks) que usted construye |
| AWS | AWS Budgets (+ acciones de presupuesto) | Notifica; las acciones deben configurarse |
| Google | Cloud Billing budgets & alerts | Notifica; el corte automático requiere automatización propia |
| Su gateway | `BudgetTracker` | **Sí**, bloquea con 429 |

## 6. Etiquetado y asignación
Etiquete recursos por servicio/entorno/equipo (*tags/labels*) para asignar costos; sin etiquetas no hay *showback*.

## 7. Calculadoras oficiales (use precios reales)
- AWS Pricing Calculator · Azure Pricing Calculator · Google Cloud Pricing Calculator (enlaces en `09-referencias.md`).
- Los precios del repositorio (`finops/data/catalogo_ilustrativo.json`) **no son reales**.

## 8. Ejercicio integrador
Con sus propios supuestos (tokens por solicitud, volumen, tps medido en el laboratorio 1): ¿API o autogestionado? ¿Qué compromiso? ¿Qué alertas? Presente la decisión como un ADR.
