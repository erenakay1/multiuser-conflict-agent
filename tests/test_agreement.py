from pathlib import Path

import pytest

from mucon.eval.agreement import (
    agreement,
    append_labels,
    labels_for_scenario,
    load_labels,
    parse_annotation,
    parse_conflict_type,
)
from mucon.schemas import ConflictType, Message, MessageRole, Scenario, User, UserPersona


@pytest.fixture
def scenario() -> Scenario:
    users = [UserPersona(user=User(id=f"u{i}", name=f"U{i}")) for i in (1, 2)]
    msgs = [
        Message(id=f"m{i}", role=MessageRole.USER, user_id=f"u{1 + i % 2}", turn=i - 1, text="x")
        for i in (1, 2, 3)
    ]
    return Scenario(id="sc-1", personas=users, scripted_messages=msgs)


def test_parse_type_prefixes() -> None:
    assert parse_conflict_type("ind") == ConflictType.INDIRECT
    assert parse_conflict_type("REV") == ConflictType.REVISION
    with pytest.raises(ValueError):
        parse_conflict_type("r")  # range / revision belirsiz


def test_parse_annotation() -> None:
    out = parse_annotation("1-3 direct, 2-3 ra", 3)
    assert out == {frozenset((1, 3)): ConflictType.DIRECT, frozenset((2, 3)): ConflictType.RANGE}
    assert parse_annotation("  ", 3) == {}
    for bad in ("1-1 direct", "1-4 direct", "1-2", "1-2 direct, 2-1 range", "a-b direct"):
        with pytest.raises(ValueError):
            parse_annotation(bad, 3)


def test_labels_roundtrip_and_agreement(scenario: Scenario, tmp_path: Path) -> None:
    a = labels_for_scenario(scenario, {frozenset((1, 3)): ConflictType.DIRECT}, "yusuf")
    assert len(a) == 3 and sum(lb.has_conflict for lb in a) == 1
    path = tmp_path / "yusuf.jsonl"
    append_labels(path, a)
    assert load_labels(path) == a

    rep = agreement(a, a)
    assert rep.binary_kappa == 1.0 and rep.type_accuracy == 1.0 and not rep.disagreements

    b = labels_for_scenario(scenario, {frozenset((1, 3)): ConflictType.RANGE}, "eren")
    rep = agreement(a, b)
    assert rep.binary_accuracy == 1.0 and rep.type_accuracy == pytest.approx(2 / 3)
    assert len(rep.disagreements) == 1
