"""LLMClient — Ollama (geliştirme) ve OpenAI (deney) için ortak arayüz.

Her iki sağlayıcı da OpenAI uyumlu Chat Completions API'si sunduğundan tek bir
`openai.OpenAI` istemcisi, sağlayıcıya göre farklı `base_url`/`api_key` ile kullanılır.
"""

from __future__ import annotations

import json
import time
from enum import StrEnum
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, ValidationError

from mucon.config import AppConfig
from mucon.schemas import TokenUsage

T = TypeVar("T", bound=BaseModel)


class Provider(StrEnum):
    OLLAMA = "ollama"
    OPENAI = "openai"


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMError(RuntimeError):
    """LLM çağrısı veya yapılandırılmış çıktı doğrulaması başarısız oldu."""


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
        client: Any | None = None,
    ) -> None:
        """`client` yalnızca testler içindir: `chat.completions.create` sunan herhangi bir nesne."""
        self.provider = provider
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_s = timeout_s
        self.total_usage = TokenUsage()
        self.n_calls = 0
        self._client = client

    def _get_client(self) -> Any:
        if self._client is None:
            import openai

            self._client = openai.OpenAI(
                base_url=self.base_url, api_key=self.api_key, timeout=self.timeout_s
            )
        return self._client

    @classmethod
    def from_config(cls, cfg: AppConfig, *, experiment: bool = False) -> LLMClient:
        """Config'ten istemci kurar. `experiment=True` → EXPERIMENT_MODEL, aksi halde DEV_MODEL."""
        llm = cfg.llm
        provider = Provider(llm.provider)
        if provider == Provider.OLLAMA:
            base_url: str | None = llm.ollama_base_url
            api_key = "ollama"  # Ollama anahtar istemez ama openai istemcisi boş kabul etmez
        else:
            base_url = None
            if llm.openai_api_key is None or not llm.openai_api_key.get_secret_value():
                raise LLMError("LLM_PROVIDER=openai için OPENAI_API_KEY gerekli (.env)")
            api_key = llm.openai_api_key.get_secret_value()
        return cls(
            provider,
            llm.experiment_model if experiment else llm.dev_model,
            base_url=base_url,
            api_key=api_key,
            temperature=llm.temperature,
            max_tokens=llm.max_tokens,
            timeout_s=llm.timeout_s,
        )

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        """Serbest metin yanıtı döndürür ve `total_usage`'ı günceller."""
        return self._complete(
            messages, temperature=temperature, max_tokens=max_tokens, seed=seed, json_mode=False
        )

    def _complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None,
        max_tokens: int | None,
        seed: int | None,
        json_mode: bool,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [m.model_dump() for m in messages],
            "temperature": self.temperature if temperature is None else temperature,
        }
        tokens = self.max_tokens if max_tokens is None else max_tokens
        if tokens is not None:
            kwargs["max_tokens"] = tokens
        if seed is not None:
            kwargs["seed"] = seed
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        start = time.perf_counter()
        try:
            resp = self._get_client().chat.completions.create(**kwargs)
        except Exception as e:  # ağ/sağlayıcı hataları tek tipe indirgenir
            raise LLMError(f"{self.provider}/{self.model} çağrısı başarısız: {e}") from e
        latency = time.perf_counter() - start

        usage = TokenUsage(
            prompt_tokens=getattr(resp.usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(resp.usage, "completion_tokens", 0) or 0,
        )
        self.total_usage = TokenUsage(
            prompt_tokens=self.total_usage.prompt_tokens + usage.prompt_tokens,
            completion_tokens=self.total_usage.completion_tokens + usage.completion_tokens,
        )
        self.n_calls += 1
        return LLMResponse(
            text=resp.choices[0].message.content or "",
            model=getattr(resp, "model", None) or self.model,
            usage=usage,
            latency_s=latency,
        )

    def structured(
        self,
        messages: list[ChatMessage],
        schema: type[T],
        *,
        temperature: float | None = None,
        seed: int | None = None,
        max_retries: int = 2,
    ) -> T:
        """Yanıtı verilen pydantic şemasına göre doğrulanmış nesne olarak döndürür.

        JSON modu açılır ve şema sistem mesajına eklenir. Doğrulama başarısızsa hata mesajı
        konuşmaya eklenerek en fazla `max_retries` kez yeniden denenir.
        """
        schema_note = ChatMessage(
            role="system",
            content="Respond ONLY with a JSON object that conforms to this JSON schema:\n"
            + json.dumps(schema.model_json_schema(), ensure_ascii=False),
        )
        convo = [schema_note, *messages]
        last_error = ""
        for _ in range(max_retries + 1):
            resp = self._complete(
                convo, temperature=temperature, max_tokens=None, seed=seed, json_mode=True
            )
            try:
                return schema.model_validate_json(resp.text)
            except ValidationError as e:
                last_error = str(e)
                convo = [
                    *convo,
                    ChatMessage(role="assistant", content=resp.text),
                    ChatMessage(
                        role="user",
                        content=f"Your JSON was invalid:\n{last_error}\nReturn a corrected JSON.",
                    ),
                ]
        raise LLMError(
            f"{max_retries + 1} denemede geçerli {schema.__name__} alınamadı: {last_error}"
        )
