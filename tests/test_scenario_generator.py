import itertools
from collections import Counter
from pathlib import Path

import pytest

from mucon.env.event_planning import VenueDB, find_feasible_plan, generate_mock_venues
from mucon.schemas import ConflictType, Scenario
from mucon.sim.scenario_generator import ScenarioGenerator


@pytest.fixture(scope="module")
def db() -> VenueDB:
    return VenueDB(generate_mock_venues(90, 7))


@pytest.fixture(scope="module")
def scenarios(db: VenueDB) -> list[Scenario]:
    return ScenarioGenerator(7, db=db).generate(40)


def kind(sc: Scenario) -> str:
    return sc.description.split("kind=")[1]


def test_reproducible(db: VenueDB, scenarios: list[Scenario]) -> None:
    assert ScenarioGenerator(7, db=db).generate(40) == scenarios
    assert ScenarioGenerator(8, db=db).generate(40) != scenarios


def test_balanced_kinds(scenarios: list[Scenario]) -> None:
    counts = Counter(kind(sc) for sc in scenarios)
    assert sum(counts[t.value] for t in ConflictType) == 20
    assert all(counts[t.value] == 5 for t in ConflictType)


def test_labels_cover_all_pairs_and_match_kind(scenarios: list[Scenario]) -> None:
    for sc in scenarios:
        msgs = sc.user_messages()
        assert len(sc.gold_labels) == len(msgs) * (len(msgs) - 1) // 2
        assert {m.user_id for m in msgs} == {p.user.id for p in sc.personas}
        assert len(sc.gold_constraints) == len(msgs)
        positives = [lb for lb in sc.gold_labels if lb.has_conflict]
        if kind(sc) in {t.value for t in ConflictType}:
            assert len(positives) == 1 and positives[0].conflict_type == kind(sc)
        else:
            assert positives == []


def test_labels_consistent_with_environment(db: VenueDB, scenarios: list[Scenario]) -> None:
    for sc in scenarios:
        by_msg = {c.source_message_id: c for c in sc.gold_constraints}
        conflict_pairs = {frozenset(lb.message_ids) for lb in sc.gold_labels if lb.has_conflict}
        for m1, m2 in itertools.combinations(by_msg, 2):
            feasible = find_feasible_plan([by_msg[m1], by_msg[m2]], db) is not None
            assert feasible != (frozenset((m1, m2)) in conflict_pairs), (sc.id, m1, m2)
        if kind(sc) in ("none", "near_miss", "revision"):
            final = [c for p in sc.personas for c in p.hidden_preferences]
            assert find_feasible_plan(final, db) is not None


def test_revision_same_user_old_first(scenarios: list[Scenario]) -> None:
    for sc in (s for s in scenarios if kind(s) == "revision"):
        lb = next(lb for lb in sc.gold_labels if lb.has_conflict)
        old, new = (next(m for m in sc.scripted_messages if m.id == i) for i in lb.message_ids)
        assert old.user_id == new.user_id and old.turn < new.turn
        hidden = {c.source_message_id for p in sc.personas for c in p.hidden_preferences}
        assert old.id not in hidden and new.id in hidden


def test_save_load(tmp_path: Path, scenarios: list[Scenario]) -> None:
    ScenarioGenerator.save(scenarios[:3], tmp_path)
    assert ScenarioGenerator.load(tmp_path) == scenarios[:3]
