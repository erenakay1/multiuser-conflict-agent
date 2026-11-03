"""Zero-shot LLM dedektörü: konuşma geçmişini LLM'e verip çakışmaları sorar."""

from __future__ import annotations

from typing import ClassVar

from mucon.detect.base import ConflictDetector
from mucon.llm.client import LLMClient
from mucon.schemas import Conflict, Session


class LLMZeroShotDetector(ConflictDetector):
    name: ClassVar[str] = "llm_zero_shot"

    def __init__(self, llm: LLMClient, *, prompt_template: str | None = None) -> None:
        self.llm = llm
        self.prompt_template = prompt_template

    def detect(self, session: Session) -> list[Conflict]:
        # TODO(H5): zero-shot dedektör — LLMClient.structured ile çakışma listesi
        raise NotImplementedError
