# AWS · Agente con Amazon Bedrock (consola) y Strands + AgentCore (código)

## Prerrequisitos
- Cuenta de AWS con créditos de prueba y **presupuesto/alerta** configurados (AWS Budgets).
- AWS CLI v2 con **SSO** (`aws configure sso`; `aws sso login`). No use claves de acceso de larga duración.
- **Acceso al modelo** en Amazon Bedrock para su región (consola de Bedrock → modelos). La disponibilidad depende de región y cuenta.
- Región sugerida: `us-east-1`.

## Parte 1 · Crear el agente desde la consola de Bedrock (≈ 25 min)
1. Consola de Bedrock → **Agents → Create agent**. Nombre: `capacity-advisor-console`. (La consola permite crearlo sin información adicional y completarlo después.)
2. Elija el **modelo** del agente y pegue las **instrucciones** (de `strands_agentcore/agent.py`, variable `SYSTEM_PROMPT`).
3. **Action group** (opcional, recomendado para ver el concepto): *Edit in Agent builder → Action groups → Add*. Defina una función `estimate_gpu_fit` con los parámetros (`model`, `quantization`, `context_tokens`, `concurrent_sequences`, `gpu_memory_gb`) y use **Return Control** (el agente devuelve el control a su aplicación para ejecutar la función, sin necesidad de crear una Lambda).
4. **Prepare** el agente, pruébelo en el panel de prueba y cree un **alias**.
5. Anote **Agent ID** y **Alias ID**.

**Invocar desde código (puente consola → código):**
```bash
cd cloud_agents/aws/bedrock_agents_boto3
pip install -r requirements.txt
export AWS_REGION=us-east-1 BEDROCK_AGENT_ID=<ID> BEDROCK_AGENT_ALIAS_ID=<ALIAS>
python invoke_agent.py "¿Qué es el KV cache?"
```

## Parte 2 · Strands Agents SDK + Bedrock AgentCore (código)
AWS tiene **dos caminos** para agentes administrados; conózcalos:

| | Bedrock **Agents** (consola) | **Strands + AgentCore Runtime** (código) |
|---|---|---|
| Enfoque | Configuración declarativa | Su código, desplegado en un runtime serverless |
| Frameworks | El propio servicio | Strands, LangGraph, Google ADK, OpenAI Agents… |
| Control | Medio | Alto |

```bash
cd cloud_agents/aws/strands_agentcore
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && set -a && source .env && set +a
aws sso login
python agent.py                           # levanta el agente en http://localhost:8080
```
En otra terminal:
```bash
curl -s -X POST localhost:8080/invocations -H 'Content-Type: application/json' \
  -d '{"prompt": "¿Cabe Llama 3.1 8B en FP16 en una GPU de 24 GB con 8 conversaciones de 8192 tokens?"}'
```
**Contrato de AgentCore Runtime:** el agente expone `POST /invocations` y `GET /ping`; el decorador `@app.entrypoint` lo resuelve por usted.

### Despliegue (opcional, genera costo)
```bash
bash deploy.sh
```
Usa el *starter toolkit* (`agentcore configure` → `agentcore launch`), el flujo de la guía oficial. La documentación más reciente también muestra un CLI nuevo (`agentcore create/deploy`):
si su versión difiere, siga `agentcore --help` y <https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-toolkit.html>.
Para observabilidad, habilite **CloudWatch Transaction Search** como indica la guía.

### Medir latencia del modelo administrado
```bash
export BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0     # use uno habilitado en SU cuenta
python ../../managed_latency/aws_bedrock_ttft.py --runs 5
```

## Seguridad y permisos mínimos
- El rol IAM del agente debe permitir **solo** `bedrock:InvokeModel*` del modelo necesario (y lo que su herramienta requiera): evite `AdministratorAccess`.
- Valide el tamaño del `prompt` (ya se hace en `agent.py`) para acotar el consumo.
- Active **Bedrock Guardrails** en producción (complementa los guardrails heurísticos del backend).

## Solución de problemas
| Problema | Causa / solución |
|---|---|
| `AccessDeniedException` al invocar el modelo | No habilitó el acceso al modelo en su región, o el rol no tiene permiso |
| `ValidationException: on-demand throughput isn't supported` | Use un **perfil de inferencia** (prefijo `us.`) en `BEDROCK_MODEL_ID` |
| `agentcore: command not found` | `pip install -r requirements.txt` con el entorno virtual activo |
| Credenciales expiradas | `aws sso login` |

## Limpieza (importante)
1. Bedrock → Agents: elimine **alias** y luego el **agente**.
2. Elimine la función **Lambda**, su **rol IAM** y los **logs** de CloudWatch si los creó.
3. AgentCore: elimine el **runtime** y el repositorio **ECR** creados (consola o el comando de eliminación que ofrezca su versión del CLI; revise `agentcore --help`).
4. Verifique en **Billing → Cost Explorer** que no queden recursos activos.

## Preguntas de reflexión
1. ¿Cuándo elegiría Bedrock Agents (declarativo) frente a AgentCore Runtime (su código)? ¿Qué pesa más: velocidad, control o portabilidad?
2. ¿Qué significa "Return Control" en términos de seguridad (quién ejecuta la acción)?
