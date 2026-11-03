"""S0 — Naive: tüm mesajlar tek bağlamda, çakışmalar yok sayılır."""

from __future__ import annotations

from typing import ClassVar

from mucon.schemas import Action, Conflict, Session
from mucon.strategies.base import CoordinationStrategy


class NaiveStrategy(CoordinationStrategy):
    name: ClassVar[str] = "s0_naive"

    def resolve(self, session: Session, conflicts: list[Conflict]) -> Action:
        # TODO(H4): S0 — tüm kısıtlarla PROCEED
        raise NotImplementedError
