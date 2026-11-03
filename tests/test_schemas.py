"""Şemalar örnek veriyle oluşturulabiliyor ve doğrulamalar çalışıyor mu?"""

import pytest
from pydantic import ValidationError

from mucon.config import AppConfig, ExperimentConfig
from mucon.schemas import (
    Action,
    ActionType,
    Conflict,
    ConflictLabel,
    ConflictType,
    Constraint,
    ConstraintType,
    EventPlan,
    Message,
    MessageRole,
    RunResult,
    Scenario,
    Session,
    TokenUsage,
    User,
    UserPersona,
    Venue,
)


@pytest.fixture
def scenario() -> Scenario:
    ali, ayse = User(id="u1", name="Ali"), User(id="u2", name="Ayşe")
    return Scenario(
        id="sc-0001",
        description="Doğum günü yemeği",
        personas=[
            UserPersona(
                user=ali,
                persona="Hafta içi çalışıyor",
                hidden_preferences=[
                    Constraint(id="c1", user_id="u1", type=ConstraintType.DATE, value="2026-11-06")
                ],
            ),
            UserPersona(
                user=ayse,
                hidden_preferences=[
                    Constraint(id="c2", user_id="u2", type=ConstraintType.DATE, value="2026-11-07")
                ],
            ),
        ],
        scripted_messages=[
            Message(id="m1", role=MessageRole.USER, user_id="u1", turn=0, text="Cuma olsun."),
            Message(id="m2", role=MessageRole.USER, user_id="u2", turn=1, text="Cumartesi olsun."),
        ],
        gold_labels=[
            ConflictLabel(
                scenario_id="sc-0001",
                message_ids=["m1", "m2"],
                has_conflict=True,
                conflict_type=ConflictType.DIRECT,
                annotator="yusuf",
            )
        ],
        seed=42,
    )


def test_scenario_roundtrip(scenario: Scenario) -> None:
    assert Scenario.model_validate_json(scenario.model_dump_json()) == scenario


def test_session_conflict_action_result(scenario: Scenario) -> None:
    session = Session(
        id="s1",
        scenario_id=scenario.id,
        users=[p.user for p in scenario.personas],
        messages=scenario.scripted_messages,
        constraints=[c for p in scenario.personas for c in p.hidden_preferences],
    )
    conflict = Conflict(
        id="k1",
        constraint_ids=["c1", "c2"],
        user_ids=["u1", "u2"],
        type=ConflictType.DIRECT,
        detector="rule_based",
        confidence=0.9,
    )
    action = Action(type=ActionType.CALL_VOTE, options=["2026-11-06", "2026-11-07"])
    assert action.is_interruption
    assert not Action(type=ActionType.PROCEED).is_interruption

    usage = TokenUsage(prompt_tokens=100, completion_tokens=20)
    assert usage.total_tokens == 120

    venue = Venue(id="v1", name="Mekan", location="Beşiktaş", capacity=20, price_per_person=450)
    result = RunResult(
        run_id="r1",
        experiment="example",
        scenario_id=session.id,
        strategy="s4_group_vote",
        detector="rule_based",
        seed=42,
        plan=EventPlan(venue_id=venue.id, date="2026-11-07"),
        user_satisfaction={"u1": 0.4, "u2": 1.0},
        n_interruptions=1,
        usage=usage,
        detected_conflicts=[conflict],
    )
    assert RunResult.model_validate_json(result.model_dump_json()) == result


def test_validators() -> None:
    with pytest.raises(ValidationError):  # çakışma en az iki kısıt içerir
        Conflict(id="k", constraint_ids=["c1"], user_ids=["u1"], type="direct", detector="x")
    with pytest.raises(ValidationError):  # çakışma yoksa tür verilmez
        ConflictLabel(
            scenario_id="s",
            message_ids=["m1", "m2"],
            has_conflict=False,
            conflict_type=ConflictType.DIRECT,
            annotator="a",
        )
    with pytest.raises(ValidationError):  # kullanıcı mesajı göndericisiz olamaz
        Message(id="m", role=MessageRole.USER, turn=0, text="x")
    with pytest.raises(ValidationError):  # tekrarlı kullanıcı id'si
        u = UserPersona(user=User(id="u1", name="A"))
        Scenario(id="s", personas=[u, u])


def test_config_models() -> None:
    assert AppConfig().llm.provider == "ollama"
    exp = ExperimentConfig(name="t", strategies=["s0_naive"], detectors=["rule_based"])
    assert exp.max_turns == 12
