"""Değerlendirme metrikleri: görev başarısı, P/R/F1, adalet, kesinti, maliyet."""

from __future__ import annotations

from pydantic import BaseModel

from mucon.env.event_planning import VenueDB
from mucon.schemas import Action, Conflict, ConflictLabel, EventPlan, Scenario, TokenUsage


class PRF1(BaseModel):
    precision: float
    recall: float
    f1: float
    support: int


def task_success(plan: EventPlan, scenario: Scenario, db: VenueDB) -> bool:
    """Tüm kullanıcıların tüm sert kısıtları sağlandı mı?"""
    # TODO(H4): check_hard_constraints ile
    raise NotImplementedError


def prf1(predicted: list[Conflict], gold: list[ConflictLabel]) -> PRF1:
    """Mesaj çifti düzeyinde precision/recall/F1."""
    # TODO(H5): P/R/F1 — mesaj çifti eşleştirme
    raise NotImplementedError


def fairness_min(satisfaction: dict[str, float]) -> float:
    """En az memnun kullanıcının memnuniyeti (egaliter / maximin)."""
    # TODO(H8): metrikler
    raise NotImplementedError


def fairness_gap(satisfaction: dict[str, float]) -> float:
    """Kullanıcılar arası memnuniyet farkı (max − min)."""
    # TODO(H8): metrikler
    raise NotImplementedError


def interruptions(actions: list[Action]) -> int:
    """Kullanıcıyı bölen eylem sayısı (soru, uzlaşma önerisi, oylama)."""
    # TODO(H8): Action.is_interruption sayımı
    raise NotImplementedError


def cost(usage: TokenUsage, *, usd_per_1k_prompt: float, usd_per_1k_completion: float) -> float:
    """Token kullanımının USD maliyeti."""
    # TODO(H8): maliyet hesabı
    raise NotImplementedError
