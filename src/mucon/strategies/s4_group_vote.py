"""S4 — Grup onayı: seçenekleri oylamaya sunar (çoğunluk oylaması veya Borda count)."""

from __future__ import annotations

from typing import ClassVar, Literal

from mucon.schemas import Action, Conflict, Session
from mucon.strategies.base import CoordinationStrategy

VoteMethod = Literal["majority", "borda"]


class GroupVoteStrategy(CoordinationStrategy):
    name: ClassVar[str] = "s4_group_vote"

    def __init__(self, method: VoteMethod = "majority") -> None:
        self.method = method

    def resolve(self, session: Session, conflicts: list[Conflict]) -> Action:
        # TODO(H7): S4 — CALL_VOTE, oylar toplandıktan sonra kazanan seçenek
        raise NotImplementedError


def majority_vote(ballots: dict[str, str]) -> str:
    """{user_id: seçenek} → kazanan seçenek (eşitlik bozma kuralı belgelenmeli)."""
    # TODO(H7): çoğunluk oylaması
    raise NotImplementedError


def borda_count(rankings: dict[str, list[str]]) -> dict[str, int]:
    """{user_id: [en iyi → en kötü]} → {seçenek: Borda puanı}."""
    # TODO(H7): Borda count
    raise NotImplementedError
