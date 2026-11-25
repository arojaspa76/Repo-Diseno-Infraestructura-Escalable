# Azure · Agente con Microsoft Foundry (consola) y 4 frameworks (código)

> **Nombres (verificado el 24-nov-2026):** *Azure AI Foundry* ahora es **Microsoft Foundry**; los roles se llaman *Foundry User, Foundry Owner,
> Foundry Account Owner, Foundry Project Manager* (antes *Azure AI …*). Fuente: documentación de Foundry Agent Service.

## Prerrequisitos
- Suscripción de **prueba** de Azure (los créditos se agotan; no actualice a pago por uso si no lo desea).
- Azure CLI: <https://learn.microsoft.com/cli/azure/install-azure-cli> → `az login`.
- Un **proyecto de Foundry** con un **modelo desplegado** (pasos abajo). La disponibilidad de modelos y cuotas depende de región y suscripción: elija uno que su suscripción permita.

## Parte 1 · Crear el agente desde el portal de Foundry (≈ 20 min)
1. Entre al portal de Foundry y **cree un proyecto** (o use uno existente).
2. **Despliegue un modelo de chat** (menú *Build → Deployments* / catálogo de modelos). Anote el **nombre del despliegue**.
3. Copie desde *Overview* el **Project endpoint** (`https://<recurso>.services.ai.azure.com/api/projects/<proyecto>`).
4. Abra **Agents → Create agent** y cree un **prompt agent** (sin código): nombre `capacity-advisor-portal`, el modelo desplegado y las instrucciones de `agent_framework/agent.py` (variable `INSTRUCTIONS`).
5. Pruebe en el **playground**: *"¿Qué es el KV cache y por qué crece con el contexto?"*

> Los *prompt agents* se definen solo con configuración (instrucciones, modelo, herramientas); Agent Service se encarga de la orquestación y el alojamiento.

## Parte 2 · Cuatro frameworks, el mismo agente

| # | Carpeta | Framework | Cuándo usarlo |
|---|---|---|---|
| 1 | `agent_framework/` | **Microsoft Agent Framework** (recomendado) | Proyectos nuevos |
| 2 | `semantic_kernel/` | Semantic Kernel | Código existente |
| 3 | `autogen/` | AutoGen | Código/investigación existente |
| 4 | `langgraph/` | LangGraph (vía LangChain `create_agent`) | Equipos del ecosistema LangChain |

Cada carpeta es independiente:
```bash
cd cloud_agents/azure/agent_framework        # o semantic_kernel / autogen / langgraph
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && set -a && source .env && set +a    # cargue variables (rellene sus valores)
az login
python agent.py                                              # o: python agent.py "su pregunta"
```
**Resultado esperado (los 4):** el agente llama a `estimate_gpu_fit` y concluye que FP16 no cabe en 24 GB (≈ 24.5 GB) y Q8_0 sí (≈ 17.5 GB).

**Autenticación:** todos usan **Microsoft Entra ID** vía `DefaultAzureCredential`/`AzureCliCredential` (sin claves). Su usuario necesita un rol sobre el recurso (p. ej. *Foundry User* / *Cognitive Services OpenAI User*).

### Comparación rápida de los cuatro
| Aspecto | MAF | Semantic Kernel | AutoGen | LangGraph |
|---|---|---|---|---|
| Herramientas | Funciones Python con tipos | Clase *plugin* con `@kernel_function` | Funciones Python | Funciones Python |
| Estilo | Agente + cliente de Foundry | Servicio + agente | Agente conversacional (`AssistantAgent`) | Grafo de estado compilado |
| Estado oficial | Recomendado (v1.0) | Vigente, migración a MAF | Sucedido por MAF | Independiente |
| Hosting en Foundry | Sí (hosted agents, vista previa) | Vía contenedor | Vía contenedor | Vía contenedor |

### Medir latencia del modelo administrado
```bash
pip install openai azure-identity
export AZURE_OPENAI_ENDPOINT=https://<recurso>.openai.azure.com/ AZURE_OPENAI_DEPLOYMENT=<despliegue>
python ../../managed_latency/azure_openai_ttft.py --runs 5
```

## Seguridad y permisos mínimos
- Asigne roles **a nivel del recurso/proyecto**, no de la suscripción.
- Para producción use **Managed Identity** (sin `az login`) y red privada (Private Endpoints).
- Active el monitoreo de **trazas** (Application Insights / Foundry) y revise que los *prompts* no guarden datos sensibles.

## Solución de problemas
| Problema | Causa / solución |
|---|---|
| `DefaultAzureCredential failed` | Ejecute `az login`; verifique la suscripción con `az account show` |
| 401/403 | Su usuario no tiene rol sobre el recurso; pida *Foundry User* o equivalente |
| `DeploymentNotFound` | El nombre del despliegue no coincide (use el **nombre del despliegue**, no el del modelo) |
| `ModuleNotFoundError: httpx` con Semantic Kernel | Ya incluido en su `requirements.txt` (la versión probada lo importa sin declararlo) |
| Error de versión de API | Ajuste `AZURE_OPENAI_API_VERSION` a una soportada por su recurso |

## Limpieza (importante)
```bash
az group list -o table
az group delete --name <su-grupo-de-recursos> --yes --no-wait     # elimina TODO el contenido del grupo
```
Si el proyecto de Foundry está en un grupo compartido, elimine el proyecto, el despliegue del modelo y el agente desde el portal.

## Preguntas de reflexión
1. ¿Por qué Microsoft unificó Semantic Kernel y AutoGen en un solo framework? ¿Qué implica para un equipo con código en SK?
2. ¿Qué cambia entre un *prompt agent* del portal y un agente en código en términos de pruebas, versionado y revisión de seguridad?
