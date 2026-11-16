from pathlib import Path

import pytest

from mucon.config import DEFAULT_CONFIG_PATH, load_config, load_experiment_config


def test_default_config_loads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("LLM_PROVIDER", "DEV_MODEL", "EXPERIMENT_MODEL", "OPENAI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    cfg = load_config(DEFAULT_CONFIG_PATH, env_file=tmp_path / "missing.env")
    assert cfg.llm.provider == "ollama"
    assert cfg.generation.n_users_min == 2


def test_env_file_and_environ_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = tmp_path / ".env"
    env.write_text("LLM_PROVIDER=openai\nDEV_MODEL=from-file\nOPENAI_API_KEY=\n")
    monkeypatch.setenv("DEV_MODEL", "from-environ")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cfg = load_config(DEFAULT_CONFIG_PATH, env_file=env)
    assert cfg.llm.provider == "openai"
    assert cfg.llm.dev_model == "from-environ"  # gerçek ortam değişkeni .env'i ezer
    assert cfg.llm.openai_api_key is None  # boş değer yok sayılır


def test_experiment_config() -> None:
    exp = load_experiment_config(Path("configs/experiments/example.yaml"))
    assert exp.name == "example" and "s0_naive" in exp.strategies
