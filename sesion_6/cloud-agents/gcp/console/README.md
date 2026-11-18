# A1 · Agente simple desde la consola de Google Cloud (Agent Designer)

**Estado:** guía basada en la documentación oficial; **no ejecutada** por el autor en una cuenta real. La interfaz cambia: si una etiqueta difiere, siga la documentación oficial enlazada en `docs/09-referencias.md`.

## Objetivo
Crear sin código un agente con instrucciones y ver cómo la consola puede generar el código ADK equivalente.

## Prerrequisitos
Proyecto de Google Cloud con facturación habilitada (o créditos de prueba), API de Vertex AI habilitada, rol IAM con permiso para usar Vertex AI (por ejemplo, *Vertex AI User*).

## Pasos (alto nivel)
1. En la consola de Google Cloud, abra la plataforma de agentes (Vertex AI / Gemini Enterprise Agent Platform) y busque **Agent Designer**.
2. **Create agent**: nombre `asesor-finops`; elija un modelo Gemini disponible en su región.
3. Pegue como instrucciones el texto de `INSTRUCTIONS` en `../../common/finops_tools.py`.
4. Pruebe en el panel de vista previa: *«Explica en tres puntos qué es rightsizing»*.
5. Use **Get code** para ver el equivalente en ADK y compárelo con `../adk_agent/finops_agent/agent.py`.

> Las dos herramientas de cálculo **no** se pueden crear sin código en este flujo; el agente de consola responde solo con conocimiento del modelo. Esa diferencia es el punto didáctico: sin herramientas, un LLM puede equivocarse en la aritmética.

## Resultado esperado
Respuesta conceptual correcta, pero que no ejecuta cálculos exactos.

## Seguridad
Mínimo privilegio: use una cuenta de servicio o su usuario con solo el rol necesario. No comparta el agente públicamente.

## Costos
El uso de Gemini se factura por token; una prueba de unas pocas preguntas es de centavos o menos, pero verifique la tarifa vigente en la calculadora oficial. Configure una alerta de presupuesto antes de empezar.

## Limpieza
Elimine el agente creado y revise **Billing → Reports** al día siguiente.

## Reflexión
¿Qué ganó y qué perdió al diseñar el agente por consola frente al código ADK (A2)? ¿Cómo versionaría y revisaría el agente en un equipo?
