# Google Cloud · Agente con Agent Studio (consola) y ADK (código)

> **Nombres (verificado el 24-nov-2026):** la documentación de Google describe la **Gemini Enterprise Agent Platform** como "una evolución de Vertex AI".
> Los diseñadores visuales aparecen como **Agent Studio** (antes *Agent Designer*) y el runtime administrado como **Agent Runtime** (antes/también *Vertex AI Agent Engine*).
> Si su consola muestra otros nombres, busque el equivalente. Fuente: <https://docs.cloud.google.com/agent-builder/overview>

## Prerrequisitos
- Cuenta de Google Cloud con **crédito de prueba** y un proyecto nuevo (no use el de producción de su empresa).
- Facturación habilitada (necesaria incluso con créditos) y **alerta de presupuesto** creada.
- `gcloud` instalado y `gcloud auth login` ejecutado.

## Parte 1 · Crear el agente desde la consola (≈ 15 min)
1. En la consola de Google Cloud, abra la página **Agents** de la plataforma de agentes (busque "Agent Platform" o "Agent Studio" en el buscador superior).
2. Pulse **Create agent**: se abre el lienzo de **Agent Studio**.
3. Configure:
   - **Nombre:** `capacity-advisor-console`
   - **Instrucciones:** pegue el prompt de `cloud_agents/gcp/adk_agent/capacity_advisor/agent.py` (variable `INSTRUCTION`).
   - **Modelo:** un modelo Gemini disponible en su región (elija uno de la lista; evite el más caro para pruebas).
   - **Herramientas:** puede añadir *Google Search* o un almacén de datos; **no son necesarias** para esta parte (la consola no ejecutará nuestras funciones Python: eso es lo que añade el código en la Parte 2).
4. Use el panel de **vista previa / chat** y pregunte: *"¿Qué es el KV cache y por qué crece con el contexto?"*
5. Pulse **Get code** y observe el código ADK que genera la consola: es el puente entre "clics" y "código".

**Para discutir:** ¿qué NO puede hacer el agente de la consola que sí hace el de la Parte 2? (respuesta: ejecutar *nuestras* herramientas con lógica exacta.)

## Parte 2 · Agente con ADK (código)
```bash
cd cloud_agents/gcp/adk_agent
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp capacity_advisor/.env.example capacity_advisor/.env     # edite según la opción A o B
```
**Opción A (rápida): Gemini API con clave.** Cree una clave en Google AI Studio y póngala en `.env` como `GOOGLE_API_KEY`.
**Opción B (empresarial): Vertex AI con credenciales de Google Cloud** (sin claves en archivos):
```bash
gcloud auth application-default login
# en .env:  GOOGLE_GENAI_USE_VERTEXAI=TRUE  GOOGLE_CLOUD_PROJECT=<proyecto>  GOOGLE_CLOUD_LOCATION=us-central1
```
> La Opción A coincide con el quickstart oficial verificado. Los nombres de variables de la Opción B son los del SDK `google-genai`; confírmelos en la guía de ADK para Vertex AI si su versión cambió.

**Ejecutar:**
```bash
adk run capacity_advisor                      # chat en terminal
adk web --port 8000                           # interfaz de desarrollo en http://localhost:8000 (SOLO desarrollo)
python run_programmatic.py                    # desde Python (útil para integrarlo en FastAPI)
```
**Resultado esperado:** el agente llama a `estimate_gpu_fit` y responde que FP16 no cabe (≈ 24.5 GB) y Q8_0 sí (≈ 17.5 GB).

### Despliegue (opcional, genera costo)
```bash
export PROJECT_ID=<su-proyecto>
bash deploy_agent_engine.sh
```
Usa `adk deploy agent_engine` (documentado en <https://adk.dev/deploy/agent-engine/deploy/>). Confirme los *flags* con `adk deploy agent_engine --help`: pueden variar entre versiones.

### Medir latencia del modelo administrado
```bash
pip install google-genai
python ../../managed_latency/gcp_gemini_ttft.py --runs 5
```

## Seguridad y permisos mínimos
- Use **cuenta de servicio dedicada** con solo los roles necesarios (p. ej. *Vertex AI User*); no use *Owner*.
- `adk web` es **solo para desarrollo**: no lo exponga a Internet.

## Solución de problemas
| Problema | Causa / solución |
|---|---|
| `adk: command not found` | Active el entorno virtual (`source .venv/bin/activate`) |
| 403 / `PERMISSION_DENIED` | Falta el rol o la API de Vertex AI: `gcloud services enable aiplatform.googleapis.com` |
| `404 model not found` | El nombre de modelo no existe en su región: defina `ADK_MODEL` con uno vigente |
| `Missing key inputs argument` | Falta `.env` o no se cargó: ejecute desde `cloud_agents/gcp/adk_agent` |

## Limpieza (importante)
1. Consola → Agent Platform → elimine el agente/instancia desplegada (Agent Runtime / Agent Engine).
2. Elimine buckets de *staging* creados por el despliegue.
3. Si usó un proyecto de prueba: `gcloud projects delete <su-proyecto>` (elimina todo lo que contiene).
4. Revoque la clave de AI Studio si la creó.

## Preguntas de reflexión
1. ¿Qué ventaja tiene que Agent Studio ofrezca *Get code*? ¿Qué riesgo de gobierno hay si los agentes solo existen en la consola?
2. ¿Qué diferencia hay entre `adk web` y un despliegue en Agent Runtime desde el punto de vista de seguridad, escalado y observabilidad?
