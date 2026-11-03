"""Gizli tercihli kullanıcılardan oluşan etkinlik planlama senaryoları üretir."""

from __future__ import annotations

from pathlib import Path

from mucon.llm.client import LLMClient
from mucon.schemas import Scenario


class ScenarioGenerator:
    """Seed'li senaryo üreteci. Çakışma oranı ve kullanıcı sayısı ayarlanabilir."""

    def __init__(
        self,
        seed: int,
        *,
        llm: LLMClient | None = None,
        n_users_range: tuple[int, int] = (2, 4),
        conflict_rate: float = 0.5,
    ) -> None:
        self.seed = seed
        self.llm = llm
        self.n_users_range = n_users_range
        self.conflict_rate = conflict_rate

    def generate(self, n: int) -> list[Scenario]:
        """`n` senaryo üretir."""
        # TODO(H3): scenario generator (şablon + opsiyonel LLM ile persona/mesaj üretimi)
        raise NotImplementedError

    @staticmethod
    def save(scenarios: list[Scenario], out_dir: Path) -> list[Path]:
        """Her senaryoyu `<out_dir>/<id>.json` olarak kaydeder."""
        # TODO(H3): JSON serileştirme
        raise NotImplementedError

    @staticmethod
    def load(in_dir: Path) -> list[Scenario]:
        """Bir klasördeki tüm senaryoları yükler."""
        # TODO(H3): JSON okuma + doğrulama
        raise NotImplementedError
