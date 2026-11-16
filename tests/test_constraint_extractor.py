import json

from mucon.extract.constraint_extractor import ConstraintExtractor, score_extraction
from mucon.llm.client import LLMClient, Provider
from mucon.schemas import (
    Constraint,
    ConstraintType,
    Message,
    MessageRole,
    Operator,
    Session,
    User,
)
from tests.fakes import FakeOpenAI

SESSION = Session(id="s", scenario_id="sc", users=[User(id="u1", name="Ali")])
MSG = Message(id="m1", role=MessageRole.USER, user_id="u1", turn=0, text='Under "500" TL please')


def test_extract_assigns_ids_and_source() -> None:
    reply = {"constraints": [{"type": "budget", "operator": "lte", "value": 500}]}
    fake = FakeOpenAI([json.dumps(reply)])
    ex = ConstraintExtractor(LLMClient(Provider.OLLAMA, "m", client=fake), seed=3)
    out = ex.extract(MSG, SESSION)
    assert len(out) == 1
    c = out[0]
    assert (c.user_id, c.source_message_id, c.type, c.operator) == (
        "u1",
        "m1",
        ConstraintType.BUDGET,
        Operator.LTE,
    )
    prompt = fake.calls[0]["messages"][-1]["content"]
    assert "Ali" in prompt and "2026-12-04" in prompt and fake.calls[0]["seed"] == 3


def test_extract_safe_returns_none_on_bad_output() -> None:
    ex = ConstraintExtractor(LLMClient(Provider.OLLAMA, "m", client=FakeOpenAI(["x", "y", "z"])))
    assert ex.extract_safe(MSG, SESSION) is None


def _c(t: ConstraintType, op: Operator, v: object, mid: str = "m1") -> Constraint:
    return Constraint(id="c", user_id="u", type=t, operator=op, value=v, source_message_id=mid)  # type: ignore[arg-type]


def test_score_extraction() -> None:
    gold = [
        _c(ConstraintType.BUDGET, Operator.LTE, 500.0),
        _c(ConstraintType.DATE, Operator.EQ, "2026-12-04", "m2"),
    ]
    pred = [
        _c(ConstraintType.BUDGET, Operator.LTE, "500"),
        _c(ConstraintType.DATE, Operator.EQ, "2026-12-05", "m2"),
    ]
    s = score_extraction(gold, pred, n_messages=2)
    assert s.type_precision == s.type_recall == 1.0
    assert s.exact_precision == s.exact_recall == 0.5
