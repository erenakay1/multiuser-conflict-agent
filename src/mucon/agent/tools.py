"""Agent'ın çağırabildiği ortam araçları (mock mekan DB üzerinde)."""

from __future__ import annotations

from typing import Any

from mucon.env.event_planning import VenueDB
from mucon.schemas import Venue


def search_venues(
    db: VenueDB,
    *,
    date: str | None = None,
    max_price: float | None = None,
    location: str | None = None,
    diet: list[str] | None = None,
    min_capacity: int | None = None,
) -> list[Venue]:
    """Filtrelere uyan mekanları arar."""
    # TODO(H4): VenueDB.search sarmalayıcısı
    raise NotImplementedError


def check_price(db: VenueDB, venue_id: str, n_people: int) -> float:
    """Toplam fiyatı döndürür."""
    # TODO(H4): fiyat hesabı
    raise NotImplementedError


def check_availability(db: VenueDB, venue_id: str, date: str) -> bool:
    """Mekan verilen tarihte müsait mi?"""
    # TODO(H4): müsaitlik kontrolü
    raise NotImplementedError


def tool_specs() -> list[dict[str, Any]]:
    """Araçların LLM'e verilecek JSON şema tanımları (OpenAI tools formatı)."""
    # TODO(H4): araç şemaları
    raise NotImplementedError
