"""Pydantic şemaları — projedeki tüm veri yapılarının tek doğruluk kaynağı.

Diğer modüller kendi veri sınıflarını tanımlamaz; buradaki modelleri kullanır.
Tarih/saat değerleri ISO formatında string olarak tutulur ("2026-11-06", "19:30").
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Enum'lar
# ---------------------------------------------------------------------------


class ConstraintType(StrEnum):
    """Etkinlik planlama alanındaki kısıt öznitelikleri."""

    DATE = "date"
    TIME = "time"
    BUDGET = "budget"
    LOCATION = "location"
    DIET = "diet"
    CAPACITY = "capacity"
    ACCESSIBILITY = "accessibility"
    ACTIVITY = "activity"
    OTHER = "other"


class Operator(StrEnum):
    """Kısıtın değerle ilişkisi."""

    EQ = "eq"
    NEQ = "neq"
    LTE = "lte"
    GTE = "gte"
    IN = "in"
    NOT_IN = "not_in"


class Strength(StrEnum):
    HARD = "hard"
    SOFT = "soft"


class ConflictType(StrEnum):
    """Çakışma türleri (taslak).

    TODO(H2): Yusuf'un çakışma türleri ve etiketleme kılavuzuyla senkronize et.
    """

    DIRECT = "direct"  # aynı öznitelik, uyuşmaz değer (cuma vs cumartesi)
    RANGE = "range"  # sayısal aralıklar kesişmiyor (bütçe ≤500 vs ≥800)
    INDIRECT = "indirect"  # farklı öznitelikler, ortam üzerinden çakışıyor (vegan + steakhouse)
    REVISION = "revision"  # aynı kullanıcının önceki talimatıyla çelişki


class MessageRole(StrEnum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class ActionType(StrEnum):
    """Koordinasyon stratejisinin agent'a verdiği karar."""

    PROCEED = "proceed"  # mevcut kısıtlarla devam et
    ASK_CLARIFICATION = "ask_clarification"  # kullanıcılara soru sor
    PROPOSE_COMPROMISE = "propose_compromise"  # uzlaşma önerisi sun
    CALL_VOTE = "call_vote"  # grup oylaması başlat
    APPLY_OVERRIDE = "apply_override"  # bir kısıtı diğerine üstün tut


INTERRUPTING_ACTIONS: frozenset[ActionType] = frozenset(
    {ActionType.ASK_CLARIFICATION, ActionType.PROPOSE_COMPROMISE, ActionType.CALL_VOTE}
)

ConstraintValue = str | int | float | bool | list[str]


# ---------------------------------------------------------------------------
# Çekirdek modeller
# ---------------------------------------------------------------------------


class Constraint(_Model):
    """Bir kullanıcı mesajından çıkarılmış yapılandırılmış kısıt."""

    id: str
    user_id: str
    type: ConstraintType
    operator: Operator = Operator.EQ
    value: ConstraintValue
    strength: Strength = Strength.HARD
    weight: float = Field(1.0, ge=0.0, description="Yumuşak kısıtlar için memnuniyet ağırlığı")
    source_message_id: str | None = None
    raw_text: str | None = None


class User(_Model):
    """Oturumdaki bir kullanıcı (agent'ın görebildiği kısım)."""

    id: str
    name: str
    rank: int = Field(
        0, description="Yalnızca S2 (yetki hiyerarşisi) baseline'ı için; eşit yetkide hepsi 0"
    )


class UserPersona(_Model):
    """Simüle kullanıcı: görünür kullanıcı + agent'tan gizli tercihler."""

    user: User
    persona: str = Field("", description="LLM simülasyonu için kısa karakter tanımı")
    hidden_preferences: list[Constraint] = Field(default_factory=list)


class Message(_Model):
    id: str
    role: MessageRole
    user_id: str | None = None
    turn: int = Field(ge=0)
    text: str
    timestamp: datetime | None = None

    @model_validator(mode="after")
    def _user_message_has_sender(self) -> Message:
        if self.role == MessageRole.USER and self.user_id is None:
            raise ValueError("role='user' olan mesajın user_id'si olmalı")
        return self


class Conflict(_Model):
    """Bir dedektörün tespit ettiği çakışma."""

    id: str
    constraint_ids: list[str] = Field(min_length=2)
    user_ids: list[str] = Field(min_length=1)
    type: ConflictType
    detector: str
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    message_ids: list[str] = Field(default_factory=list)
    description: str = ""


class ConflictLabel(_Model):
    """İnsan (gold) etiketi: bir mesaj çifti çakışıyor mu?"""

    scenario_id: str
    message_ids: list[str] = Field(min_length=2)
    has_conflict: bool
    conflict_type: ConflictType | None = None
    annotator: str
    notes: str = ""

    @model_validator(mode="after")
    def _type_iff_conflict(self) -> ConflictLabel:
        if self.has_conflict and self.conflict_type is None:
            raise ValueError("has_conflict=True ise conflict_type zorunlu")
        if not self.has_conflict and self.conflict_type is not None:
            raise ValueError("has_conflict=False ise conflict_type boş olmalı")
        return self


class Scenario(_Model):
    """Bir grup etkinlik planlama senaryosu (simülasyon girdisi)."""

    id: str
    domain: Literal["event_planning"] = "event_planning"
    description: str = ""
    personas: list[UserPersona] = Field(min_length=2)
    scripted_messages: list[Message] = Field(
        default_factory=list, description="Dedektör değerlendirmesi için sabit diyalog (opsiyonel)"
    )
    gold_labels: list[ConflictLabel] = Field(default_factory=list)
    seed: int | None = None

    @model_validator(mode="after")
    def _unique_users(self) -> Scenario:
        ids = [p.user.id for p in self.personas]
        if len(ids) != len(set(ids)):
            raise ValueError("Senaryodaki kullanıcı id'leri benzersiz olmalı")
        return self


class Session(_Model):
    """Agent'ın gördüğü canlı oturum durumu (gizli tercihler yok)."""

    id: str
    scenario_id: str
    users: list[User] = Field(min_length=1)
    messages: list[Message] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Ortam ve agent çıktıları
# ---------------------------------------------------------------------------


class Venue(_Model):
    """Mock mekan veritabanı kaydı."""

    id: str
    name: str
    location: str
    capacity: int = Field(gt=0)
    price_per_person: float = Field(ge=0.0)
    diet_options: list[str] = Field(default_factory=list)
    available_dates: list[str] = Field(default_factory=list)
    accessible: bool = False
    tags: list[str] = Field(default_factory=list)


class EventPlan(_Model):
    """Agent'ın nihai planı."""

    venue_id: str | None = None
    date: str | None = None
    start_time: str | None = None
    budget_per_person: float | None = None
    diet: list[str] = Field(default_factory=list)
    notes: str = ""


class Action(_Model):
    """Koordinasyon stratejisinin çıktısı."""

    type: ActionType
    message: str = Field("", description="Kullanıcılara gösterilecek agent metni")
    active_constraint_ids: list[str] = Field(default_factory=list)
    dropped_constraint_ids: list[str] = Field(default_factory=list)
    target_user_ids: list[str] = Field(default_factory=list)
    options: list[str] = Field(default_factory=list, description="Oylama/uzlaşma seçenekleri")

    @property
    def is_interruption(self) -> bool:
        return self.type in INTERRUPTING_ACTIONS


class TokenUsage(_Model):
    prompt_tokens: int = Field(0, ge=0)
    completion_tokens: int = Field(0, ge=0)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class RunResult(_Model):
    """Tek bir (senaryo × strateji × dedektör) koşusunun sonucu."""

    run_id: str
    experiment: str
    scenario_id: str
    strategy: str
    detector: str
    seed: int
    plan: EventPlan | None = None
    task_success: bool = False
    user_satisfaction: dict[str, float] = Field(default_factory=dict)
    n_turns: int = Field(0, ge=0)
    n_interruptions: int = Field(0, ge=0)
    latency_s: float = Field(0.0, ge=0.0)
    usage: TokenUsage = Field(default_factory=TokenUsage)
    detected_conflicts: list[Conflict] = Field(default_factory=list)
    error: str | None = None
