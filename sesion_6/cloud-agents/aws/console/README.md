# A9 · Agente simple desde la consola de AWS (Amazon Bedrock AgentCore)

**Estado:** guía basada en documentación oficial; **no ejecutada** por el autor en una cuenta real. Nombres de menú sujetos a cambio.

> **Aviso de vigencia:** Bedrock Agents «clásico» deja de estar disponible para clientes nuevos (fecha oficial consultada: 2026-07-30). Para cuentas nuevas el camino es **AgentCore**. No siga tutoriales antiguos del agente clásico.

## Objetivo
Crear un agente en la consola con AgentCore (flujo de *harness*) y probarlo en el *playground*.

## Prerrequisitos
Cuenta AWS con un usuario/rol de IAM (no la cuenta raíz), región que ofrezca AgentCore y acceso al modelo elegido en Bedrock.

## Pasos (alto nivel)
1. En la consola, abra Amazon Bedrock AgentCore y entre a **Build → Harness**.
2. Elija creación **Quick** (valores por defecto) o **Advanced** (control de rol y modelo).
3. Indique el modelo y pegue `INSTRUCTIONS` de `../../common/finops_tools.py` como instrucciones del sistema.
4. Pruebe en el **playground**.

## Resultado esperado
Respuesta conceptual; sin herramientas propias no hará cálculos exactos.

## Seguridad
Rol de ejecución con mínimo privilegio (solo invocar el modelo necesario). Active CloudTrail. Nunca use claves de acceso del usuario raíz.

## Costos
Se cobra por uso del modelo y de los componentes de AgentCore; **consulte la página de precios vigente** y configure **AWS Budgets** con alerta (recuerde que alerta, no detiene).

## Limpieza
Elimine el harness/agente y los roles creados; revise Cost Explorer al día siguiente.

## Reflexión
¿Qué responsabilidades pasan a AWS y cuáles siguen siendo suyas (modelo de responsabilidad compartida) cuando usa un servicio administrado de agentes?
