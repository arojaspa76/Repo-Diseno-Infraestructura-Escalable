# A5 · Microsoft Agent Framework (MAF) — la opción recomendada en Azure

**Estado:** validado offline (construcción del agente con agent-framework-core 1.26.0 y agent-framework-foundry 1.16.2). **Ejecución real: pendiente.**

MAF unifica lo mejor de Semantic Kernel y AutoGen y es el camino para código nuevo.

## Ejecución
```bash
cd cloud-agents/azure/maf
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
az login
python agent_maf.py "Compara on-demand, compromiso y spot para 2 instancias de 1 USD/h con 30% y 65% de descuento."
```
Resultado esperado: la respuesta incluye 1,460 (on-demand), 1,022 (compromiso) y 562.1 USD/mes (spot) provenientes de la herramienta.

> Instale `agent-framework-core` y `agent-framework-foundry`, **no** el meta-paquete `agent-framework`: en la fecha de validación el meta-paquete no resolvía por dependencias en versión preliminar.

## Pruebas offline / Seguridad / Costos
`pytest -q test_smoke.py`. Entra ID vía `AzureCliCredential`. Costos: tokens del modelo.

## Problemas
`ModuleNotFoundError`: instaló el meta-paquete. `AuthenticationError`: ejecute `az login`.

## Limpieza
No crea recursos persistentes; elimine el deployment del modelo si ya no lo necesita.

## Reflexión
Compare con A6 (SK) y A7 (AutoGen): ¿qué conceptos se mantienen y cuáles se renombran?
