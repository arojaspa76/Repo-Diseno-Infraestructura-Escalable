# ADR-002 · Comenzar con API administrada y revaluar por volumen
- **Estado:** Propuesto
- **Contexto:** Con 200.000 solicitudes/mes (supuesto) y utilización baja de GPU, el costo fijo de autogestionar supera el pago por token (cifras ilustrativas del simulador).
- **Decisión:** Iniciar con API administrada; revaluar cuando el volumen mensual supere el punto de equilibrio medido con precios reales y utilización real.
- **Consecuencias:** + menor riesgo operativo inicial; − dependencia del proveedor y de su política de datos; se mitiga con la abstracción de proveedor.
- **Gatillo de revisión:** volumen sostenido > punto de equilibrio, requisitos de residencia de datos o latencia no alcanzables.
