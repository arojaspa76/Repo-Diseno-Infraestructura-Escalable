# Solución de problemas

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `/health` = `degraded` | Ollama apagado o URL incorrecta | `ollama serve`; revise `OLLAMA_BASE_URL` |
| 401 en `/v1/chat` | `GATEWAY_API_KEYS` definido y falta `X-API-Key` | Envíe la cabecera o vacíe la variable (solo dev) |
| El gateway no arranca con `ENVIRONMENT=prod` | Falla cerrado sin claves | Defina `GATEWAY_API_KEYS` |
| 429 en pruebas de carga | Rate limit o presupuesto | Suba `RATE_LIMIT_PER_MINUTE` y el presupuesto (lab 6) |
| 400 `prompt_injection_suspected` en frase legítima | Falso positivo | Ajuste `INJECTION_BLOCK_THRESHOLD` |
| Aviso `httpx`/`httpx2` en pruebas | Cambio en Starlette | Inofensivo |
| `pip` falla con `agent-framework` | Meta-paquete en versión preliminar | Instale `agent-framework-core` y `agent-framework-foundry` |
| `ModuleNotFoundError: httpx` (Semantic Kernel) | Dependencia no declarada por SK | Use el `requirements.txt` del ejemplo |
| `DeploymentNotFound` (Azure) | Nombre de modelo en vez de deployment | Use el nombre del deployment |
| 404 de modelo (Gemini) | ID inexistente en su región | Copie uno vigente de Model Garden |
| `AccessDenied` (Bedrock) | Modelo no habilitado o sin perfil de inferencia | Habilite acceso; use perfil de inferencia |
| Docker Compose falla | **No se probó** en la preparación | Revise logs con `docker compose logs`; reporte el problema |
