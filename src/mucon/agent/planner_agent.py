"""ReAct tarzı planlama agent'ı: çıkar → tespit et → koordine et → araç çağır → planla."""

from __future__ import annotations

from mucon.detect.base import ConflictDetector
from mucon.env.event_planning import VenueDB
from mucon.extract.constraint_extractor import ConstraintExtractor
from mucon.llm.client import LLMClient
from mucon.schemas import Action, EventPlan, Message, Session
from mucon.strategies.base import CoordinationStrategy


class PlannerAgent:
    """Çok kullanıcılı oturumda etkinlik planlayan agent."""

    def __init__(
        self,
        llm: LLMClient,
        extractor: ConstraintExtractor,
        detector: ConflictDetector,
        strategy: CoordinationStrategy,
        venue_db: VenueDB,
        *,
        max_steps: int = 8,
    ) -> None:
        self.llm = llm
        self.extractor = extractor
        self.detector = detector
        self.strategy = strategy
        self.venue_db = venue_db
        self.max_steps = max_steps

    def on_message(self, session: Session, message: Message) -> Action:
        """Yeni kullanıcı mesajını işler ve agent'ın eylemini döndürür."""
        # TODO(H4): temel döngü (S0 ile); TODO(H7): dedektör + strateji entegrasyonu
        raise NotImplementedError

    def finalize(self, session: Session) -> EventPlan:
        """Aktif kısıtlar ve araç sonuçlarıyla nihai planı üretir (ReAct döngüsü)."""
        # TODO(H4): ReAct döngüsü — tools.py araçlarıyla
        raise NotImplementedError
