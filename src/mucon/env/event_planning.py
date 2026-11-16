"""Grup etkinlik planlama ortamı: mock mekan veritabanı + sert kısıt denetleyicisi.

Mock mekanlar sağduyu kurallarına uyacak şekilde üretilir; INDIRECT çakışmalar bu kurallardan
doğar ve etiketleyicinin ortam veritabanına bakmadan da tanıyabileceği türdendir:

- steakhouse mekanlarında vegan ve vejetaryen seçenek yoktur,
- fine_dining kişi başı en az 900 TL'dir,
- rooftop_bar tekerlekli sandalye erişimine uygun değildir,
- escape_room en fazla 8 kişiliktir.
"""

from __future__ import annotations

import json
import random
from collections.abc import Iterable
from datetime import date, timedelta
from pathlib import Path

from mucon.schemas import (
    Constraint,
    ConstraintType,
    ConstraintValue,
    EventPlan,
    Operator,
    Strength,
    Venue,
)

LOCATIONS: tuple[str, ...] = ("Kadıköy", "Beşiktaş", "Şişli", "Üsküdar", "Beyoğlu", "Sarıyer")
DIETS: tuple[str, ...] = ("vegan", "vegetarian", "halal", "gluten_free")
TIME_SLOTS: tuple[str, ...] = tuple(f"{h:02d}:00" for h in range(10, 24))

# etkinlik türü → (kişi başı fiyat aralığı TL, kapasite aralığı)
ACTIVITIES: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
    "cafe": ((150, 400), (10, 60)),
    "dinner": ((300, 800), (10, 120)),
    "steakhouse": ((700, 1500), (10, 80)),
    "fine_dining": ((900, 2500), (10, 40)),
    "bowling": ((300, 600), (10, 60)),
    "karaoke": ((300, 700), (6, 40)),
    "escape_room": ((400, 700), (4, 8)),
    "rooftop_bar": ((500, 1200), (20, 120)),
    "cinema": ((200, 400), (20, 200)),
}

DEFAULT_WINDOW_START = "2026-12-04"  # cuma
DEFAULT_WINDOW_DAYS = 10


def planning_window(
    start: str = DEFAULT_WINDOW_START, days: int = DEFAULT_WINDOW_DAYS
) -> list[str]:
    """Planlama penceresindeki ISO tarihler."""
    d0 = date.fromisoformat(start)
    return [(d0 + timedelta(days=i)).isoformat() for i in range(days)]


class VenueDB:
    """Bellek içi mock mekan veritabanı."""

    def __init__(self, venues: list[Venue]) -> None:
        self.venues = venues
        self._by_id = {v.id: v for v in venues}

    @classmethod
    def from_json(cls, path: Path) -> VenueDB:
        """`data/processed/venues.json` dosyasından yükler."""
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls([Venue.model_validate(v) for v in raw])

    def to_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [v.model_dump(mode="json") for v in self.venues]
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def get(self, venue_id: str) -> Venue:
        """Id ile mekan döndürür; yoksa KeyError."""
        return self._by_id[venue_id]

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
        """Filtrelere uyan mekanları döndürür (diet: listedeki tüm seçenekler sunulmalı)."""
        out: list[Venue] = []
        for v in self.venues:
            if date is not None and date not in v.available_dates:
                continue
            if max_price is not None and v.price_per_person > max_price:
                continue
            if location is not None and v.location != location:
                continue
            if diet and not set(diet) <= set(v.diet_options):
                continue
            if min_capacity is not None and v.capacity < min_capacity:
                continue
            if accessible is not None and v.accessible != accessible:
                continue
            out.append(v)
        return out


def generate_mock_venues(
    n: int, seed: int, *, window_start: str = DEFAULT_WINDOW_START, window_days: int = 10
) -> list[Venue]:
    """Tekrarlanabilir rastgele mock mekan listesi üretir (sağduyu kuralları modül başında)."""
    rng = random.Random(seed)
    dates = planning_window(window_start, window_days)
    activities = list(ACTIVITIES)
    venues: list[Venue] = []
    for i in range(n):
        activity = activities[i % len(activities)]  # her türden dengeli sayıda mekan
        (pmin, pmax), (cmin, cmax) = ACTIVITIES[activity]
        diets = [d for d in DIETS if rng.random() < 0.5]
        if activity == "steakhouse":
            diets = [d for d in diets if d not in ("vegan", "vegetarian")]
        accessible = activity != "rooftop_bar" and rng.random() < 0.6
        venues.append(
            Venue(
                id=f"v{i + 1:03d}",
                name=f"{activity.replace('_', ' ').title()} {i + 1}",
                location=rng.choice(LOCATIONS),
                capacity=rng.randint(cmin, cmax),
                price_per_person=float(rng.randrange(pmin, pmax + 1, 50)),
                diet_options=diets,
                available_dates=sorted(d for d in dates if rng.random() < 0.7),
                accessible=accessible,
                tags=[activity],
            )
        )
    return venues


# ---------------------------------------------------------------------------
# Kısıt değerlendirmesi
# ---------------------------------------------------------------------------


def _as_list(value: ConstraintValue) -> list[str]:
    return [str(x) for x in value] if isinstance(value, list) else [str(value)]


def _compare_scalar(actual: str | float | bool, op: Operator, value: ConstraintValue) -> bool:
    """Tek değerli öznitelik (tarih, saat, fiyat, kapasite, konum, erişim) karşılaştırması."""
    if op in (Operator.IN, Operator.NOT_IN):
        inside = str(actual) in _as_list(value)
        return inside if op == Operator.IN else not inside
    if isinstance(value, list):
        raise ValueError(f"{op} operatörü liste değer alamaz: {value}")
    if op == Operator.EQ:
        return actual == value if isinstance(actual, bool) else str(actual) == str(value)
    if op == Operator.NEQ:
        return actual != value if isinstance(actual, bool) else str(actual) != str(value)
    # LTE / GTE: sayılar sayısal, ISO tarih/saat stringleri sözlük sırasıyla karşılaştırılır
    if isinstance(actual, int | float) and not isinstance(actual, bool):
        a: float | str = float(actual)
        b: float | str = float(value)
    else:
        a, b = str(actual), str(value)
    return a <= b if op == Operator.LTE else a >= b  # type: ignore[operator]


def _compare_set(offered: Iterable[str], op: Operator, value: ConstraintValue) -> bool:
    """Küme değerli öznitelik (diyet seçenekleri, etkinlik etiketleri) karşılaştırması."""
    offered_set = set(offered)
    wanted = set(_as_list(value))
    if op == Operator.EQ:
        return wanted <= offered_set
    if op == Operator.IN:
        return bool(wanted & offered_set)
    if op in (Operator.NEQ, Operator.NOT_IN):
        return not (wanted & offered_set)
    raise ValueError(f"{op} operatörü küme değerli öznitelikte desteklenmiyor")


def satisfies(plan: EventPlan, constraint: Constraint, db: VenueDB) -> bool:
    """Plan tek bir kısıtı sağlıyor mu?

    Gerekli bilgi planda yoksa (ör. mekan seçilmemiş) False döner. `OTHER` türü denetlenemez
    ve her zaman True kabul edilir.
    """
    c, op = constraint, constraint.operator
    venue = db.get(plan.venue_id) if plan.venue_id else None
    match c.type:
        case ConstraintType.DATE:
            return plan.date is not None and _compare_scalar(plan.date, op, c.value)
        case ConstraintType.TIME:
            return plan.start_time is not None and _compare_scalar(plan.start_time, op, c.value)
        case ConstraintType.BUDGET:
            price = venue.price_per_person if venue else plan.budget_per_person
            return price is not None and _compare_scalar(price, op, c.value)
        case ConstraintType.LOCATION:
            return venue is not None and _compare_scalar(venue.location, op, c.value)
        case ConstraintType.DIET:
            return venue is not None and _compare_set(venue.diet_options, op, c.value)
        case ConstraintType.CAPACITY:
            return venue is not None and _compare_scalar(venue.capacity, op, c.value)
        case ConstraintType.ACCESSIBILITY:
            return venue is not None and _compare_scalar(venue.accessible, op, c.value)
        case ConstraintType.ACTIVITY:
            return venue is not None and _compare_set(venue.tags, op, c.value)
        case ConstraintType.OTHER:
            return True


def check_hard_constraints(
    plan: EventPlan, constraints: list[Constraint], db: VenueDB
) -> list[Constraint]:
    """Planın ihlal ettiği sert kısıtları döndürür (boş liste = tümü sağlandı)."""
    return [c for c in constraints if c.strength == Strength.HARD and not satisfies(plan, c, db)]


def find_feasible_plan(constraints: list[Constraint], db: VenueDB) -> EventPlan | None:
    """Tüm kısıtları birlikte sağlayan bir plan arar (mekan × uygun tarih × saat); yoksa None.

    Senaryo üreteci bunu çakışma yok / çakışma var garantisini doğrulamak için kullanır.
    """
    for venue in db.venues:
        for d in venue.available_dates:
            for t in TIME_SLOTS:
                plan = EventPlan(
                    venue_id=venue.id,
                    date=d,
                    start_time=t,
                    budget_per_person=venue.price_per_person,
                )
                if all(satisfies(plan, c, db) for c in constraints):
                    return plan
    return None
