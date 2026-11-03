"""LLMClient — Ollama (geliştirme) ve OpenAI (deney) için ortak arayüz.

Her iki sağlayıcı da OpenAI uyumlu Chat Completions API'si sunduğundan tek bir
`openai.OpenAI` istemcisi, sağlayıcıya göre farklı `base_url`/`api_key` ile kullanılır.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, TypeVar

from pydantic import BaseModel

from mucon.config import AppConfig
from mucon.schemas import TokenUsage

T = TypeVar("T", bound=BaseModel)


class Provider(StrEnum):
    OLLAMA = "ollama"
    OPENAI = "openai"


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMResponse(BaseModel):
    text: str
    model: str
    usage: TokenUsage
    latency_s: float


class LLMClient:
    """Sağlayıcıdan bağımsız LLM istemcisi."""

    def __init__(
        self,
        provider: Provider,
        model: str,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        timeout_s: float = 60.0,
    ) -> None:
        self.provider = provider
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_s = timeout_s
        self.total_usage = TokenUsage()

    @classmethod
    def from_config(cls, cfg: AppConfig, *, experiment: bool = False) -> LLMClient:
        """Config'ten istemci kurar. `experiment=True` → EXPERIMENT_MODEL, aksi halde DEV_MODEL."""
        # TODO(H3): provider seçimi, base_url/api_key çözümü
        raise NotImplementedError

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        """Serbest metin yanıtı döndürür ve `total_usage`'ı günceller."""
        # TODO(H3): openai.OpenAI(...).chat.completions.create + gecikme/token ölçümü
        raise NotImplementedError

    def structured(
        self,
        messages: list[ChatMessage],
        schema: type[T],
        *,
        temperature: float | None = None,
        seed: int | None = None,
        max_retries: int = 2,
    ) -> T:
        """Yanıtı verilen pydantic şemasına göre doğrulanmış nesne olarak döndürür."""
        # TODO(H3): JSON mode / response_format + pydantic doğrulama + retry
        raise NotImplementedError
