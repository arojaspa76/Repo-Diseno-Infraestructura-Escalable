# Guía del estudiante · Sesión 6

## Resultados de aprendizaje (medibles)
Al terminar usted podrá: (1) comparar on-demand, compromiso y spot para un caso dado y justificar la elección con cifras; (2) dimensionar una flota usando p95, N+1 y SLO; (3) calcular el punto de equilibrio entre API administrada y autogestionada; (4) diseñar presupuestos y alertas y explicar qué no detienen; (5) mapear controles a OWASP LLM Top 10 2026; (6) leer y ejecutar un agente en Google, Azure y AWS.

## Glosario
- **Token:** fragmento de texto que el modelo procesa; unidad de cobro de las APIs.
- **TTFT:** tiempo hasta el primer token. **TPOT:** tiempo por token de salida. **Throughput:** tokens (o solicitudes) por segundo.
- **Prefill / decode / KV cache:** procesar el prompt / generar tokens uno a uno / memoria que evita recalcular el contexto.
- **SLI/SLO/SLA:** indicador medido / objetivo interno / compromiso contractual. **Error budget:** margen de fallo permitido por el SLO.
- **On-demand, Reserved/Commitment, Spot:** ver `04-finops-llm.md`.
- **Rightsizing:** ajustar el tamaño del recurso a la demanda real.
- **N+1:** una unidad extra para tolerar la falla de una.
- **Gateway:** punto único de entrada con controles transversales.
- **Denial of Wallet:** ataque que busca agotar su presupuesto.
- **Agente:** LLM + instrucciones + herramientas, con ciclo de decisión.

## Ejercicios (sin soluciones; las del docente van en el repositorio privado)
1. (E1) Con `scenario`, ¿cuántas horas de pico al mes hacen que comprometer la base **y** el pico deje de ser mala idea? Documente su método.
2. (E2) Genere su propio CSV de utilización con un pico semanal y recomiende tamaño. ¿Qué otro dato pediría?
3. (E3) Diseñe niveles de alerta distintos para clientes «estudiante» y «profesor» y justifique.
4. (E4) Proponga tres cargas útiles que eludan `scan_prompt_injection` y tres controles de otra capa que limiten el daño.
5. (A1–A10) Elija una nube, cree el agente por consola y por código, y compare esfuerzo, control y seguridad.
6. Mida tokens/s en su equipo (lab 1) y recalcule capacidad para 100 usuarios.

## Autoevaluación
1. ¿Por qué el promedio de utilización puede llevar a subdimensionar?
2. ¿En qué situación el modelo de compromiso es **peor** que on-demand?
3. ¿Qué ocurre con una carga sincrónica de usuarios en una instancia spot cuando llega el aviso de interrupción?
4. Un presupuesto de Azure llegó al 100 %: ¿se detuvo el gasto? ¿Qué haría para que ocurra?
5. ¿Qué riesgo OWASP 2026 mitiga el límite de tokens de salida?
6. ¿Por qué el servidor descarta los mensajes `system` del cliente?
7. ¿Qué cambió entre Semantic Kernel/AutoGen y Microsoft Agent Framework y qué implica para su código existente?
8. ¿Qué diferencia hay entre el costo sombra de API y el costo de cómputo propio en el gateway?

## Lecturas
FinOps Framework (finops.org) · OWASP GenAI Security Project · documentación oficial de cada nube (ver `09-referencias.md`).
