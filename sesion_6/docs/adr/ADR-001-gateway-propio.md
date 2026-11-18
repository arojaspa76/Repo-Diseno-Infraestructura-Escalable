# ADR-001 · Gateway propio delante del modelo
- **Estado:** Propuesto (para discusión en clase)
- **Contexto:** Las nubes ofrecen alertas de presupuesto y filtros de contenido, pero no un límite duro por cliente alineado a nuestro SLO, ni medición de costo sombra comparable entre proveedores.
- **Decisión:** Todo tráfico pasa por un gateway que autentica, limita, aplica presupuesto, filtra entrada/salida y emite métricas.
- **Alternativas:** (a) llamar al proveedor directo desde cada aplicación; (b) usar solo el gateway administrado de la nube.
- **Consecuencias:** + control y portabilidad; − un componente más que operar y asegurar (réplicas, estado de presupuesto compartido).
