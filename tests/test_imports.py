"""Tüm modüller import edilebiliyor mu? (opsiyonel `ml` bağımlılıkları olmadan da)"""

import importlib
import pkgutil

import pytest
from typer.testing import CliRunner

import mucon
from mucon.__main__ import app

MODULES = sorted(
    m.name
    for m in pkgutil.walk_packages(mucon.__path__, prefix="mucon.")
    if m.name != "mucon.__main__"
)


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name: str) -> None:
    importlib.import_module(name)


def test_registries() -> None:
    from mucon.detect import DETECTORS
    from mucon.strategies import STRATEGIES

    assert set(STRATEGIES) == {
        "s0_naive",
        "s1_last_wins",
        "s2_hierarchy",
        "s3_compromise",
        "s4_group_vote",
    }
    assert set(DETECTORS) == {"rule_based", "llm_zero_shot", "deberta"}


def test_cli_help_lists_commands() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("generate", "detect-eval", "run", "analyze"):
        assert cmd in result.output
