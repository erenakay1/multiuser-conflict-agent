"""Fine-tune edilmiş DeBERTa/NLI dedektörü.

`transformers`/`torch` opsiyoneldir (`uv sync --extra ml`); bu yüzden import'lar
fonksiyon içinde yapılmalı, modül seviyesinde değil.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from mucon.detect.base import ConflictDetector
from mucon.schemas import Conflict, ConflictLabel, Scenario, Session


class DebertaNLIDetector(ConflictDetector):
    """Mesaj çiftlerini NLI ile sınıflar; 'contradiction' olasılığı eşiği aşarsa çakışma."""

    name: ClassVar[str] = "deberta"

    def __init__(
        self,
        model_path: str | Path = "microsoft/deberta-v3-base",
        *,
        threshold: float = 0.5,
        device: str | None = None,
    ) -> None:
        self.model_path = model_path
        self.threshold = threshold
        self.device = device

    def load(self) -> None:
        """Model ve tokenizer'ı yükler (lazy import)."""
        # TODO(H6): transformers AutoModelForSequenceClassification yükleme
        raise NotImplementedError

    def detect(self, session: Session) -> list[Conflict]:
        # TODO(H6): mesaj çiftleri üzerinde NLI çıkarımı
        raise NotImplementedError


def build_pair_dataset(scenarios: list[Scenario], labels: list[ConflictLabel]) -> object:
    """Etiketlerden (premise, hypothesis, label) çiftli eğitim veri seti kurar."""
    # TODO(H6): datasets.Dataset üretimi
    raise NotImplementedError


def finetune(train: object, eval: object, out_dir: Path, *, seed: int, epochs: int = 3) -> Path:
    """DeBERTa'yı çakışma çiftleri üzerinde fine-tune eder; checkpoint yolunu döndürür."""
    # TODO(H6): DeBERTa fine-tune (transformers Trainer)
    raise NotImplementedError
