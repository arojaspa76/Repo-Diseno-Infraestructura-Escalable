# ADR-003 · Router de modelos y caché como evolución
- **Estado:** Propuesto (no implementado)
- **Contexto:** Consultas frecuentes y simples pueden atenderse con un modelo más pequeño o con caché.
- **Decisión:** Medir primero la distribución de consultas; implementar caché exacta antes que semántica (la semántica puede devolver respuestas de otro usuario o contexto).
- **Riesgos:** fuga entre usuarios, respuestas obsoletas, mal enrutamiento que degrade calidad.
- **Consecuencias:** ahorro potencial no cuantificado hasta medir; no se promete porcentaje.
