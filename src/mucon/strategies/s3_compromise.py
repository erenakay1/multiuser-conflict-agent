"""S3 — LLM ile uzlaştırma: çakışan tercihlerin ortasını bulan öneri üretir."""

from __future__ import annotations

from typing import ClassVar

from mucon.llm.client import LLMClient
from mucon.schemas import Action, Conflict, Session
from mucon.strategies.base import CoordinationStrategy


class CompromiseStrategy(CoordinationStrategy):
    name: ClassVar[str] = "s3_compromise"

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def resolve(self, session: Session, conflicts: list[Conflict]) -> Action:
        # TODO(H6): S3 uzlaştırma — PROPOSE_COMPROMISE
        raise NotImplementedError
