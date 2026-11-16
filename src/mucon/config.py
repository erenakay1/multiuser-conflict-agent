"""YAML + .env yükleme. Ayarlar burada tanımlanan pydantic modelleriyle doğrulanır.

Öncelik: .env (ortam değişkenleri) > configs/*.yaml > model varsayılanları.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from dotenv import dotenv_values
from pydantic import BaseModel, Field, SecretStr

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "default.yaml"


class LLMSettings(BaseModel):
    provider: Literal["ollama", "openai"] = "ollama"
    dev_model: str = "llama3.1:8b"
    experiment_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434/v1"
    openai_api_key: SecretStr | None = None
    temperature: float = 0.0
    max_tokens: int | None = 1024
    timeout_s: float = 60.0


class PathSettings(BaseModel):
    data_dir: Path = Path("data")
    raw_dir: Path = Path("data/raw")
    scenarios_dir: Path = Path("data/scenarios")
    labels_dir: Path = Path("data/labels")
    processed_dir: Path = Path("data/processed")
    results_dir: Path = Path("results")
    external_dir: Path = Path("external")
    venue_db: Path = Path("data/processed/venues.json")


class GenerationSettings(BaseModel):
    """Senaryo üreteci (sim/scenario_generator.py) ayarları."""

    n_venues: int = Field(90, gt=0)
    n_users_min: int = Field(2, ge=2)
    n_users_max: int = Field(4, ge=2)
    conflict_rate: float = Field(0.5, ge=0.0, le=1.0)
    near_miss_rate: float = Field(0.5, ge=0.0, le=1.0)
    window_start: str = "2026-12-04"
    window_days: int = Field(10, gt=1)


class AppConfig(BaseModel):
    seed: int = 42
    llm: LLMSettings = Field(default_factory=LLMSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    generation: GenerationSettings = Field(default_factory=GenerationSettings)


class ExperimentConfig(BaseModel):
    name: str
    seed: int = 42
    scenarios_dir: Path = Path("data/scenarios")
    n_scenarios: int = Field(20, gt=0)
    strategies: list[str] = Field(min_length=1)
    detectors: list[str] = Field(min_length=1)
    s4_methods: list[Literal["majority", "borda"]] = Field(default_factory=lambda: ["majority"])
    max_turns: int = Field(12, gt=0)
    use_experiment_model: bool = False


DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"

# Ortam değişkeni → LLMSettings alanı
ENV_OVERRIDES: dict[str, str] = {
    "LLM_PROVIDER": "provider",
    "DEV_MODEL": "dev_model",
    "EXPERIMENT_MODEL": "experiment_model",
    "OLLAMA_BASE_URL": "ollama_base_url",
    "OPENAI_API_KEY": "openai_api_key",
}


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: YAML kökü bir sözlük olmalı")
    return data


def _env_values(env_file: Path | None) -> dict[str, str]:
    """`.env` dosyası + gerçek ortam değişkenleri (ikincisi önceliklidir). os.environ değişmez."""
    values: dict[str, str] = {}
    if env_file is not None and env_file.exists():
        values.update({k: v for k, v in dotenv_values(env_file).items() if v is not None})
    values.update({k: os.environ[k] for k in ENV_OVERRIDES if k in os.environ})
    return values


def load_config(path: Path = DEFAULT_CONFIG_PATH, env_file: Path | None = None) -> AppConfig:
    """YAML dosyasını okuyup .env/ortam değişkenleriyle ezerek AppConfig döndürür.

    `env_file` verilmezse proje kökündeki `.env` (varsa) kullanılır. Boş değerler yok sayılır.
    """
    data = _read_yaml(path)
    llm = dict(data.get("llm") or {})
    env = _env_values(env_file if env_file is not None else DEFAULT_ENV_PATH)
    for var, field in ENV_OVERRIDES.items():
        if env.get(var):
            llm[field] = env[var]
    data["llm"] = llm
    return AppConfig.model_validate(data)


def load_experiment_config(path: Path) -> ExperimentConfig:
    """configs/experiments/*.yaml dosyasını ExperimentConfig olarak yükler."""
    return ExperimentConfig.model_validate(_read_yaml(path))
