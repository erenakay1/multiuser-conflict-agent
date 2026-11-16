import pytest

from mucon.config import AppConfig, LLMSettings
from mucon.llm.client import ChatMessage, LLMClient, LLMError, Provider
from mucon.schemas import ExtractionResult
from tests.fakes import FakeOpenAI

MSG = [ChatMessage(role="user", content="hi")]


def test_from_config_ollama_and_openai() -> None:
    c = LLMClient.from_config(AppConfig())
    assert c.provider == Provider.OLLAMA and c.model == "llama3.1:8b" and c.base_url
    cfg = AppConfig(llm=LLMSettings(provider="openai"))
    with pytest.raises(LLMError):  # anahtar yok
        LLMClient.from_config(cfg, experiment=True)
    cfg = AppConfig(llm=LLMSettings(provider="openai", openai_api_key="sk-x"))
    c = LLMClient.from_config(cfg, experiment=True)
    assert c.model == "gpt-4o-mini" and c.base_url is None


def test_chat_tracks_usage() -> None:
    fake = FakeOpenAI(["hello", "again"])
    c = LLMClient(Provider.OLLAMA, "m", client=fake, max_tokens=50)
    assert c.chat(MSG, seed=1).text == "hello"
    c.chat(MSG)
    assert c.n_calls == 2 and c.total_usage.total_tokens == 30
    assert fake.calls[0]["seed"] == 1 and fake.calls[0]["max_tokens"] == 50


def test_structured_retries_then_succeeds() -> None:
    good = '{"constraints": [{"type": "date", "operator": "eq", "value": "2026-12-04"}]}'
    fake = FakeOpenAI(["not json", good])
    c = LLMClient(Provider.OLLAMA, "m", client=fake)
    out = c.structured(MSG, ExtractionResult)
    assert out.constraints[0].value == "2026-12-04"
    assert fake.calls[0]["response_format"] == {"type": "json_object"}
    assert len(fake.calls[1]["messages"]) > len(fake.calls[0]["messages"])  # hata geri bildirildi


def test_structured_gives_up() -> None:
    c = LLMClient(Provider.OLLAMA, "m", client=FakeOpenAI(["x", "y"]))
    with pytest.raises(LLMError):
        c.structured(MSG, ExtractionResult, max_retries=1)
