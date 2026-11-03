"""Çakışma dedektörü arayüzü."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from mucon.schemas import Conflict, Session


class ConflictDetector(ABC):
    """Bir oturumdaki kullanıcı talimatları arasındaki çakışmaları tespit eder."""

    name: ClassVar[str]

    @abstractmethod
    def detect(self, session: Session) -> list[Conflict]:
        """Oturumdaki tüm çakışmaları döndürür (çakışma yoksa boş liste)."""
