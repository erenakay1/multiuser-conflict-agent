"""Koordinasyon stratejisi arayüzü."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from mucon.schemas import Action, Conflict, Session


class CoordinationStrategy(ABC):
    """Tespit edilen çakışmalara karşı agent'ın ne yapacağına karar verir."""

    name: ClassVar[str]

    @abstractmethod
    def resolve(self, session: Session, conflicts: list[Conflict]) -> Action:
        """Oturum durumu ve çakışmalara göre bir sonraki `Action`'ı döndürür."""
