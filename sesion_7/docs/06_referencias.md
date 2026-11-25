# Referencias

Columna **Verif.** = ¿la fuente fue abierta/consultada durante la preparación (24-nov-2026)? "No" no significa que sea incorrecta: significa que debe verificar el enlace antes de citarla.

## Documentación oficial de proveedores y frameworks
| Tema | Fuente | Verif. |
|---|---|---|
| ADK (inicio rápido Python) | <https://adk.dev/get-started/python/> | Sí |
| ADK → Agent Engine (despliegue) | <https://adk.dev/deploy/agent-engine/deploy/> | Sí |
| Gemini Enterprise Agent Platform (visión general) | <https://docs.cloud.google.com/agent-builder/overview> | Sí |
| Agent Studio / Agent Designer (consola) | <https://docs.cloud.google.com/agent-builder/agent-designer> | Sí |
| Foundry Agent Service (visión general) | <https://learn.microsoft.com/azure/foundry/agents/overview> | Sí |
| Foundry — Responses API (quickstart) | <https://learn.microsoft.com/azure/foundry/agents/quickstarts/responses-api> | Sí |
| Foundry — hosted agents (quickstart) | <https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent> | Sí |
| Microsoft Agent Framework + Foundry | <https://learn.microsoft.com/agent-framework/agents/providers/microsoft-foundry> | Sí |
| Microsoft Agent Framework v1.0 (blog) | <https://devblogs.microsoft.com/foundry/from-local-to-production-the-complete-developer-journey-for-building-composing-and-deploying-ai-agents> | Sí |
| Semantic Kernel — ChatCompletionAgent | <https://learn.microsoft.com/semantic-kernel/frameworks/agent/agent-types/chat-completion-agent> | Sí |
| LangChain — quickstart (`create_agent`) | <https://docs.langchain.com/oss/python/langchain/quickstart> | Sí |
| Bedrock AgentCore — starter toolkit | <https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-toolkit.html> | Sí |
| Strands → AgentCore Runtime | <https://strandsagents.com/docs/user-guide/deploy/deploy_to_bedrock_agentcore/> | Sí |
| Bedrock Agents — action groups | <https://docs.aws.amazon.com/bedrock/latest/userguide/agents-action-add.html> | Sí |
| Ollama — FAQ (`keep_alive`, `num_ctx`) | <https://docs.ollama.com/faq> | Sí |
| Ollama — compatibilidad OpenAI | <https://docs.ollama.com/api/openai> | Sí |

## Seguridad y gobierno
| Tema | Fuente | Verif. |
|---|---|---|
| OWASP Top 10 for LLM Applications 2026 | <https://genai.owasp.org/top-10-for-llm-applications-2026/> | Sí (lista de riesgos) |
| OWASP Top 10 for LLM Applications 2025 | <https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/> | Sí |
| NIST AI RMF 1.0 y AI 600-1 (Generative AI Profile) | <https://www.nist.gov/itl/ai-risk-management-framework> | No |
| ISO/IEC 42001:2023 | <https://www.iso.org/standard/81230.html> | No |
| MITRE ATLAS | <https://atlas.mitre.org/> | No |

## Artículos académicos (inferencia eficiente)
| Tema | Referencia | Verif. |
|---|---|---|
| Atención / Transformer | Vaswani et al. (2017). *Attention Is All You Need*. arXiv:1706.03762 | No |
| PagedAttention / vLLM | Kwon et al. (2023). *Efficient Memory Management for LLM Serving with PagedAttention*. SOSP '23. arXiv:2309.06180 | Sí |
| Batching continuo | Yu et al. (2022). *Orca: A Distributed Serving System for Transformer-Based Generative Models*. OSDI '22 | No |
| FlashAttention | Dao et al. (2022). arXiv:2205.14135 | No |
| GQA | Ainslie et al. (2023). *GQA: Training Generalized Multi-Query Transformer Models*. arXiv:2305.13245 | No |
| Decodificación especulativa | Leviathan et al. (2022). arXiv:2211.17192 | No |
| Cuantización | Dettmers et al. (2022) LLM.int8(): arXiv:2208.07339 · Frantar et al. (2022) GPTQ: arXiv:2210.17323 · Lin et al. (2023) AWQ: arXiv:2306.00978 | No |
| Separación prefill/decode | Zhong et al. (2024) DistServe: arXiv:2401.09670 · Patel et al. (2023) Splitwise: arXiv:2311.18677 | No |

## Libros y prácticas de operación
- Beyer, Jones, Petoff, Murphy (eds.) (2016). *Site Reliability Engineering*. O'Reilly — capítulos sobre SLIs, SLOs y SLAs. (No verificado en esta sesión)
- FinOps Foundation — *FinOps Framework*: <https://www.finops.org/framework/> (No verificado en esta sesión)
