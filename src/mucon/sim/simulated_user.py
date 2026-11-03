"""LLM ile simüle edilen, gizli tercihleri olan kullanıcı."""

from __future__ import annotations

from mucon.llm.client import LLMClient
from mucon.schemas import Action, EventPlan, Message, Session, UserPersona


class SimulatedUser:
    """Gizli tercihlerine göre mesaj yazan ve agent eylemlerine yanıt veren kullanıcı."""

    def __init__(self, persona: UserPersona, llm: LLMClient, *, seed: int) -> None:
        self.persona = persona
        self.llm = llm
        self.seed = seed

    @property
    def user_id(self) -> str:
        return self.persona.user.id

    def opening_message(self, session: Session) -> Message:
        """Oturumun başında ilk talimatı üretir."""
        # TODO(H4): simülasyon altyapısı — persona + gizli tercihlerden ilk mesaj
        raise NotImplementedError

    def respond(self, session: Session, action: Action) -> Message | None:
        """Agent eylemine (soru, uzlaşma önerisi, oylama) yanıt verir; yanıt yoksa None."""
        # TODO(H4): simülasyon altyapısı — eyleme tepki
        raise NotImplementedError

    def satisfaction(self, plan: EventPlan) -> float:
        """Nihai planın bu kullanıcının gizli tercihlerine göre memnuniyeti, [0, 1]."""
        # TODO(H4): ağırlıklı kısıt sağlama oranı
        raise NotImplementedError
