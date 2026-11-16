from pathlib import Path

import pytest

from mucon.env.event_planning import (
    VenueDB,
    check_hard_constraints,
    find_feasible_plan,
    generate_mock_venues,
    satisfies,
)
from mucon.schemas import Constraint, ConstraintType, EventPlan, Operator, Strength, Venue

T, Op = ConstraintType, Operator


def c(t: ConstraintType, op: Operator, v: object, **kw: object) -> Constraint:
    return Constraint(id="c", user_id="u", type=t, operator=op, value=v, **kw)  # type: ignore[arg-type]


@pytest.fixture
def db() -> VenueDB:
    return VenueDB(
        [
            Venue(
                id="v1",
                name="A",
                location="Kadıköy",
                capacity=20,
                price_per_person=450,
                diet_options=["vegan"],
                available_dates=["2026-12-04"],
                accessible=True,
                tags=["dinner"],
            )
        ]
    )


def test_mock_venues_reproducible_and_follow_rules() -> None:
    a, b = generate_mock_venues(90, 1), generate_mock_venues(90, 1)
    assert a == b and a != generate_mock_venues(90, 2)
    for v in a:
        if "steakhouse" in v.tags:
            assert "vegan" not in v.diet_options
        if "fine_dining" in v.tags:
            assert v.price_per_person >= 900
        if "rooftop_bar" in v.tags:
            assert not v.accessible
        if "escape_room" in v.tags:
            assert v.capacity <= 8


def test_db_roundtrip_and_search(db: VenueDB, tmp_path: Path) -> None:
    path = tmp_path / "v.json"
    db.to_json(path)
    loaded = VenueDB.from_json(path)
    assert loaded.get("v1") == db.get("v1")
    assert loaded.search(location="Kadıköy", diet=["vegan"], max_price=500) == db.venues
    assert loaded.search(date="2026-12-05") == []
    with pytest.raises(KeyError):
        loaded.get("nope")


@pytest.mark.parametrize(
    ("constraint", "expected"),
    [
        (c(T.DATE, Op.EQ, "2026-12-04"), True),
        (c(T.DATE, Op.NEQ, "2026-12-04"), False),
        (c(T.DATE, Op.IN, ["2026-12-04", "2026-12-05"]), True),
        (c(T.TIME, Op.GTE, "18:00"), True),
        (c(T.TIME, Op.LTE, "18:00"), False),
        (c(T.BUDGET, Op.LTE, 500), True),
        (c(T.BUDGET, Op.GTE, 800), False),
        (c(T.LOCATION, Op.NEQ, "Beşiktaş"), True),
        (c(T.DIET, Op.EQ, "vegan"), True),
        (c(T.DIET, Op.EQ, "halal"), False),
        (c(T.CAPACITY, Op.GTE, 25), False),
        (c(T.ACCESSIBILITY, Op.EQ, True), True),
        (c(T.ACTIVITY, Op.EQ, "steakhouse"), False),
        (c(T.OTHER, Op.EQ, "anything"), True),
    ],
)
def test_satisfies(db: VenueDB, constraint: Constraint, expected: bool) -> None:
    plan = EventPlan(venue_id="v1", date="2026-12-04", start_time="19:00")
    assert satisfies(plan, constraint, db) is expected


def test_missing_venue_fails(db: VenueDB) -> None:
    assert not satisfies(EventPlan(), c(T.LOCATION, Op.EQ, "Kadıköy"), db)


def test_hard_only_and_feasibility(db: VenueDB) -> None:
    plan = EventPlan(venue_id="v1", date="2026-12-04", start_time="19:00")
    soft = c(T.BUDGET, Op.LTE, 100, strength=Strength.SOFT)
    hard = c(T.BUDGET, Op.LTE, 100)
    assert check_hard_constraints(plan, [soft, hard], db) == [hard]
    assert find_feasible_plan([c(T.DATE, Op.EQ, "2026-12-04")], db) is not None
    assert find_feasible_plan([c(T.DATE, Op.EQ, "2026-12-04"), hard], db) is None
