"""YAML + .env yükleme. Ayarlar burada tanımlanan pydantic modelleriyle doğrulanır.

Öncelik: .env (ortam değişkenleri) > configs/*.yaml > model varsayılanları.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

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


class AppConfig(BaseModel):
    seed: int = 42
    llm: LLMSettings = Field(default_factory=LLMSettings)
    paths: PathSettings = Field(default_factory=PathSettings)


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


def load_config(path: Path = DEFAULT_CONFIG_PATH, env_file: Path | None = None) -> AppConfig:
    """YAML dosyasını okuyup .env/ortam değişkenleriyle ezerek AppConfig döndürür."""
    # TODO(H3): yaml.safe_load + dotenv.load_dotenv + LLM_PROVIDER/DEV_MODEL/... override
    raise NotImplementedError


def load_experiment_config(path: Path) -> ExperimentConfig:
    """configs/experiments/*.yaml dosyasını ExperimentConfig olarak yükler."""
    # TODO(H3): yaml okuma + doğrulama
    raise NotImplementedError
