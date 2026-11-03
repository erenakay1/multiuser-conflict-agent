"""Deney döngüsü: (strateji × dedektör × senaryo) ızgarası.

Sonuçlar `results/<YYYY-MM-DD>_<deney>/` altına config kopyasıyla kaydedilir.
"""

from __future__ import annotations

from pathlib import Path

from mucon.config import AppConfig, ExperimentConfig
from mucon.detect.base import ConflictDetector
from mucon.schemas import RunResult, Scenario
from mucon.strategies.base import CoordinationStrategy


def make_results_dir(cfg: ExperimentConfig, app_cfg: AppConfig) -> Path:
    """`results/<tarih>_<deney>/` klasörünü oluşturur ve config kopyasını yazar."""
    # TODO(H7): klasör + config.yaml kopyası
    raise NotImplementedError


def estimate_cost(cfg: ExperimentConfig) -> dict[str, int]:
    """Koşu öncesi tahmini LLM çağrı ve token sayısı (API koşusundan önce onay için)."""
    # TODO(H7): çağrı/token tahmini
    raise NotImplementedError


def run_single(
    scenario: Scenario,
    strategy: CoordinationStrategy,
    detector: ConflictDetector,
    *,
    app_cfg: AppConfig,
    max_turns: int,
    seed: int,
) -> RunResult:
    """Tek senaryoyu simüle kullanıcılarla uçtan uca koşar."""
    # TODO(H7): uçtan uca pipeline
    raise NotImplementedError


def run_experiment(cfg: ExperimentConfig, app_cfg: AppConfig) -> list[RunResult]:
    """Izgaradaki tüm kombinasyonları koşar ve sonuçları kaydeder."""
    # TODO(H8): tam deney döngüsü
    raise NotImplementedError
