"""LLM ile mesajdan `Constraint` listesi çıkaran modül."""

from __future__ import annotations

from mucon.llm.client import LLMClient
from mucon.schemas import Constraint, Message, Session


class ConstraintExtractor:
    """Mesaj + oturum bağlamından yapılandırılmış kısıt çıkarır."""

    def __init__(self, llm: LLMClient, *, prompt_template: str | None = None) -> None:
        self.llm = llm
        self.prompt_template = prompt_template

    def extract(self, message: Message, session: Session) -> list[Constraint]:
        """Tek bir kullanıcı mesajındaki kısıtları döndürür."""
        # TODO(H3): kısıt çıkarıcı v0 — LLMClient.structured ile
        raise NotImplementedError
