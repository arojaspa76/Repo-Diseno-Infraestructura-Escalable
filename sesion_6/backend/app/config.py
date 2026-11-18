"""Configuración del gateway.

Toda la configuración llega por variables de entorno (o un archivo .env local).
Nunca se escriben secretos en el código. Ver `.env.example` en la raíz del repo.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Aplicación ---------------------------------------------------------
    app_name: str = "llm-gateway-s06"
    environment: str = Field(default="dev", description="dev | staging | prod")
    log_level: str = "INFO"
    # Por defecto NO se registran prompts ni respuestas (privacidad / LLM02).
    log_prompts: bool = False

    # --- Proveedor de inferencia (Ollama local) -----------------------------
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"
    request_timeout_s: float = 120.0

    # --- Seguridad ----------------------------------------------------------
    # Lista separada por comas. Vacía = autenticación desactivada (solo en dev).
    gateway_api_keys: str = ""
    max_input_chars: int = 4000
    max_output_tokens: int = 512
    rate_limit_per_minute: int = 30
    redact_pii: bool = True
    injection_block_threshold: int = 2
    cors_origins: str = "http://localhost:5173"

    # --- FinOps -------------------------------------------------------------
    # PRECIOS ILUSTRATIVOS. Sustitúyalos por los de su proveedor (ver
    # docs/04-finops-llm.md). Se usan para calcular un "costo sombra":
    # cuánto costaría la misma conversación en una API administrada.
    ref_price_input_per_mtok_usd: float = 1.00
    ref_price_output_per_mtok_usd: float = 4.00
    # Costo por hora de la infraestructura propia que atiende el modelo
    # (VM/GPU). Para Ollama en su portátil puede dejarlo en 0.
    infra_cost_per_hour_usd: float = 0.0
    # Presupuesto diario por cliente, medido en USD de costo sombra.
    daily_budget_usd_per_client: float = 0.50
    budget_alert_levels: str = "50,80,100"

    @property
    def api_keys(self) -> list[str]:
        return [k.strip() for k in self.gateway_api_keys.split(",") if k.strip()]

    @property
    def alert_levels(self) -> list[int]:
        return sorted(int(x) for x in self.budget_alert_levels.split(",") if x.strip())

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def validate_for_environment(self) -> None:
        """Falla cerrado: fuera de dev se exige autenticación configurada."""
        if self.environment != "dev" and not self.api_keys:
            raise RuntimeError(
                "GATEWAY_API_KEYS es obligatorio cuando ENVIRONMENT != 'dev'."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
