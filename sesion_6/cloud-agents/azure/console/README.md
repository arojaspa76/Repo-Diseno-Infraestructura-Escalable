# A3 · Agente simple desde el portal de Microsoft Foundry

**Estado:** guía basada en la documentación oficial; **no ejecutada** por el autor en una cuenta real. Verifique las etiquetas vigentes del portal.

## Objetivo
Crear un agente de instrucciones (*prompt agent*) en el portal, probarlo en el *playground* y obtener su endpoint para los ejemplos de código A4–A8.

## Prerrequisitos
Suscripción de Azure (la cuenta de prueba basta), un recurso y proyecto de Foundry, **un modelo desplegado** (anote el nombre del *deployment*), y su usuario con el rol **Azure AI User** sobre el proyecto.

## Pasos
1. Entre al portal de Foundry y abra su proyecto. Copie el **Project endpoint** (lo necesitará como `FOUNDRY_PROJECT_ENDPOINT`).
2. En **Models** (catálogo), despliegue un modelo disponible en su región y cuota; anote el nombre del deployment (`FOUNDRY_MODEL_DEPLOYMENT`).
3. Cree un agente nuevo, elija ese deployment y pegue `INSTRUCTIONS` de `../../common/finops_tools.py`.
4. Pruebe en el playground con la misma pregunta que en A1 y A9.

## Resultado esperado
Respuesta conceptual del agente. Sin herramientas de código no hará cálculos exactos.

## Seguridad
Prefiera **Microsoft Entra ID** a claves de API (los ejemplos de código lo hacen así). Asigne roles mínimos, no *Owner*.

## Costos (cuenta de prueba)
Los modelos se cobran por token contra su crédito. **Cree un presupuesto en Cost Management con alerta antes de desplegar**: recuerde que los presupuestos de Azure **notifican, no detienen** el gasto. Si su cuenta de prueba no tiene cuota para el modelo elegido, pruebe otra región o un modelo más pequeño.

## Limpieza
Elimine el agente y, sobre todo, el **deployment** del modelo y el grupo de recursos si ya no los usa.

## Reflexión
¿Qué rol RBAC necesita un estudiante que solo prueba frente a uno que crea recursos? ¿Qué impide que un presupuesto de Azure frene el gasto y cómo lo compensa el gateway del laboratorio 5?
