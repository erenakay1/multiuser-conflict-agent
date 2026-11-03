"""Grup etkinlik planlama ortamı: mock mekan veritabanı + sert kısıt denetleyicisi."""

from __future__ import annotations

from pathlib import Path

from mucon.schemas import Constraint, EventPlan, Venue


class VenueDB:
    """Bellek içi mock mekan veritabanı."""

    def __init__(self, venues: list[Venue]) -> None:
        self.venues = venues

    @classmethod
    def from_json(cls, path: Path) -> VenueDB:
        """`data/processed/venues.json` dosyasından yükler."""
        # TODO(H3): json okuma + Venue doğrulama
        raise NotImplementedError

    def get(self, venue_id: str) -> Venue:
        """Id ile mekan döndürür; yoksa KeyError."""
        # TODO(H3): id arama
        raise NotImplementedError

    def search(
        self,
        *,
        date: str | None = None,
        max_price: float | None = None,
        location: str | None = None,
        diet: list[str] | None = None,
        min_capacity: int | None = None,
        accessible: bool | None = None,
    ) -> list[Venue]:
        """Filtrelere uyan mekanları döndürür."""
        # TODO(H3): filtreleme
        raise NotImplementedError


def generate_mock_venues(n: int, seed: int) -> list[Venue]:
    """Tekrarlanabilir rastgele mock mekan listesi üretir."""
    # TODO(H3): seed'li mock mekan üreteci
    raise NotImplementedError


def satisfies(plan: EventPlan, constraint: Constraint, db: VenueDB) -> bool:
    """Plan tek bir kısıtı sağlıyor mu?"""
    # TODO(H3): ConstraintType × Operator değerlendirmesi
    raise NotImplementedError


def check_hard_constraints(
    plan: EventPlan, constraints: list[Constraint], db: VenueDB
) -> list[Constraint]:
    """Planın ihlal ettiği sert kısıtları döndürür (boş liste = tümü sağlandı)."""
    # TODO(H3): Strength.HARD kısıtlar üzerinde `satisfies`
    raise NotImplementedError
