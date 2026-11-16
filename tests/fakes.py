"""Testler için sahte OpenAI istemcisi (ağ çağrısı yok)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any


class FakeOpenAI:
    """`chat.completions.create` çağrılarını kaydeder, sıradaki hazır yanıtı döndürür."""

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.calls: list[dict[str, Any]] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        text = self.replies.pop(0)
        return SimpleNamespace(
            model=kwargs["model"],
            choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
        )
