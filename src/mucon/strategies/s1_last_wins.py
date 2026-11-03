"""S1 — Son talimat geçerli: çakışan kısıtlardan en son gelen tutulur."""

from __future__ import annotations

from typing import ClassVar

from mucon.schemas import Action, Conflict, Session
from mucon.strategies.base import CoordinationStrategy


class LastWinsStrategy(CoordinationStrategy):
    name: ClassVar[str] = "s1_last_wins"

    def resolve(self, session: Session, conflicts: list[Conflict]) -> Action:
        # TODO(H4): S1 — mesaj sırasına göre eski kısıtları düşür
        raise NotImplementedError
