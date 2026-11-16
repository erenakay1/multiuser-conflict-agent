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


def test_label_ui_is_blind(scenario: Scenario) -> None:
    from mucon.eval.agreement import render_label_ui
    from mucon.schemas import ConflictLabel

    secret = scenario.model_copy(
        update={
            "description": "generator kind=direct",
            "gold_labels": [
                ConflictLabel(
                    scenario_id="sc-1",
                    message_ids=["m1", "m3"],
                    has_conflict=True,
                    conflict_type=ConflictType.DIRECT,
                    annotator="generator",
                )
            ],
        }
    )
    html = render_label_ui([secret], "k")
    assert '"id": "sc-1"' in html and "/*__SCENARIOS__*/" not in html
    assert "kind=" not in html and '"generator"' not in html.split("const STORE_KEY")[0]


def test_import_export_roundtrip(scenario: Scenario, tmp_path: Path) -> None:
    from mucon.eval.agreement import labels_from_export, write_labels_replacing

    export = {
        "format": "mucon-labels-v1",
        "annotator": "Yusuf",
        "labels": {
            "sc-1": {"conflicts": [{"a": "m3", "b": "m1", "type": "direct"}], "notes": " hm "}
        },
    }
    annotator, labels = labels_from_export(export, [scenario])
    assert annotator == "yusuf" and len(labels) == 3
    pos = [lb for lb in labels if lb.has_conflict]
    assert pos[0].message_ids == ["m1", "m3"] and pos[0].notes == "hm"

    path = tmp_path / "yusuf.jsonl"
    assert write_labels_replacing(path, labels) == 3
    assert write_labels_replacing(path, labels) == 3  # tekrar içe aktarım çoğaltmaz

    for bad in (
        {**export, "format": "x"},
        {**export, "annotator": "generator"},
        {**export, "labels": {"sc-9": {"conflicts": []}}},
        {**export, "labels": {"sc-1": {"conflicts": [{"a": "m1", "b": "m9", "type": "direct"}]}}},
        {**export, "labels": {"sc-1": {"conflicts": [{"a": "m1", "b": "m2", "type": "zzz"}]}}},
    ):
        with pytest.raises(ValueError):
            labels_from_export(bad, [scenario])


def test_adjudicate(scenario: Scenario) -> None:
    from mucon.eval.agreement import adjudicate
    from mucon.schemas import AdjudicationDecision, AdjudicationRecord

    a = labels_for_scenario(scenario, {frozenset((1, 3)): ConflictType.DIRECT}, "yusuf")
    b = labels_for_scenario(scenario, {frozenset((1, 2)): ConflictType.RANGE}, "generator")

    def record(*decisions: AdjudicationDecision) -> AdjudicationRecord:
        return AdjudicationRecord(
            annotators=["yusuf", "generator"],
            decided_by=["eren"],
            date="2026-11-16",
            decisions=list(decisions),
        )

    d13 = AdjudicationDecision(
        scenario_id="sc-1", message_ids=["m1", "m3"], decision=None, rationale="x"
    )
    d12 = AdjudicationDecision(
        scenario_id="sc-1", message_ids=["m2", "m1"], decision=ConflictType.RANGE, rationale="y"
    )
    out = adjudicate(a, b, record(d13, d12))
    assert len(out) == 3 and all(lb.annotator == "adjudicated" for lb in out)
    pos = [lb for lb in out if lb.has_conflict]
    assert [(lb.message_ids, lb.conflict_type, lb.notes) for lb in pos] == [
        (["m1", "m2"], ConflictType.RANGE, "y")
    ]
    with pytest.raises(ValueError, match="eksik"):
        adjudicate(a, b, record(d13))
    d23 = AdjudicationDecision(
        scenario_id="sc-1", message_ids=["m2", "m3"], decision=None, rationale="z"
    )
    with pytest.raises(ValueError, match="Uyuşmazlık olmayan"):
        adjudicate(a, b, record(d13, d12, d23))
