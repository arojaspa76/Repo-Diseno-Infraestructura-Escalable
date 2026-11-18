# A10 · Strands Agents + Amazon Bedrock AgentCore Runtime

**Estado:** validado offline (strands-agents 1.65.0, bedrock-agentcore 1.26.0): el agente se construye, las herramientas se ejecutan y el punto de entrada valida el prompt. **Ejecución real en AWS: pendiente.**

## Arquitectura
`agent_strands.py` define el agente (modelo de Bedrock + herramientas). `agentcore_app.py` lo envuelve con `BedrockAgentCoreApp` (servidor HTTP con `/invocations` y `/ping`, puerto 8080) para desplegarlo en AgentCore Runtime.

## Prerrequisitos
Cuenta AWS, credenciales (preferible SSO/rol, no claves de larga vida), **acceso al modelo en Bedrock** y su ID (o perfil de inferencia) en `BEDROCK_MODEL_ID`.

## Ejecución local
```bash
cd cloud-agents/aws/strands_agentcore
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env     # complete BEDROCK_MODEL_ID
python agent_strands.py "Compara on-demand, compromiso y spot para 2 instancias de 1 USD/h"
python agentcore_app.py   # y en otra terminal:
curl -X POST http://localhost:8080/invocations -H 'Content-Type: application/json' -d '{"prompt":"Compara on-demand, compromiso y spot para 2 instancias de 1 USD/h"}'
```

## Despliegue
Use la CLI de AgentCore según la documentación oficial vigente (`docs/09-referencias.md`); los comandos cambian entre versiones, por eso no se fijan aquí. **No ejecutado** en este material.

## Seguridad
El punto de entrada rechaza prompts vacíos o de más de 4000 caracteres (control de consumo). Rol de ejecución con mínimo privilegio. Herramientas de solo cálculo.

## Costos
Tokens del modelo + cómputo de AgentCore Runtime mientras exista el despliegue. Configure **AWS Budgets**.

## Problemas
- `AccessDeniedException`: el modelo no está habilitado en su cuenta/región.
- «on-demand throughput isn't supported»: use un **perfil de inferencia** como ID.

## Limpieza
Elimine el runtime desplegado, repositorios de imágenes y roles creados.

## Reflexión
¿Qué ventaja operativa da separar la definición del agente (Strands) de su empaquetado (AgentCore)? ¿Qué cambia en la factura entre ejecutar local y en Runtime?
