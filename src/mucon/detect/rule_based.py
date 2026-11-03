"""Kural tabanlı dedektör: çıkarılmış kısıtları çiftler halinde karşılaştırır."""

from __future__ import annotations

from typing import ClassVar

from mucon.detect.base import ConflictDetector
from mucon.schemas import Conflict, ConflictType, Constraint, Session


class RuleBasedDetector(ConflictDetector):
    name: ClassVar[str] = "rule_based"

    def detect(self, session: Session) -> list[Conflict]:
        # TODO(H5): kural tabanlı dedektör — session.constraints üzerinde çiftli kontrol
        raise NotImplementedError

    @staticmethod
    def compare(a: Constraint, b: Constraint) -> ConflictType | None:
        """İki kısıt çakışıyorsa türünü, çakışmıyorsa None döndürür."""
        # TODO(H5): aynı ConstraintType için operatör/değer uyumsuzluğu
        raise NotImplementedError
