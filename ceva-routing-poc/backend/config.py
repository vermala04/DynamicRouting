"""Runtime configuration for the CEVA routing platform.

Centralising environment lookups keeps API handlers, optimization, and AI
reasoning code deterministic and easier to move into microservices later.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List


def _csv_env(name: str, default: str) -> List[str]:
    value = os.getenv(name, default).strip()
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "CEVA Dynamic Routing Platform")
    app_version: str = os.getenv("APP_VERSION", "1.1.0")
    environment: str = os.getenv("APP_ENV", "local")
    operating_region: str = os.getenv("OPERATING_REGION", "France")
    control_tower: str = os.getenv("CONTROL_TOWER", "CEVA France Control Tower")
    depot_timezone: str = os.getenv("DEPOT_TIMEZONE", "Europe/Paris")
    use_osrm: bool = os.getenv("USE_OSRM", "1").lower() not in {"0", "false", "no"}
    cors_origins: List[str] = field(default_factory=lambda: _csv_env("CORS_ORIGINS", "http://localhost:5173"))
    mistral_api_key: str = os.getenv("MISTRAL_API_KEY", "").strip()
    mistral_model: str = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
    ai_pattern: str = os.getenv("AI_INTELLIGENCE_PATTERN", "RAG Pipeline Engineering")
    carbon_price_eur_per_tonne: float = float(os.getenv("CARBON_PRICE_EUR_PER_TONNE", "90"))


settings = Settings()
