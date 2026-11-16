"""LLM ile mesajdan `Constraint` listesi çıkaran modül (v0: tek mesaj, zero-shot, JSON çıktı)."""

from __future__ import annotations

from collections import Counter
from datetime import date

from pydantic import BaseModel

from mucon.env.event_planning import ACTIVITIES, DIETS, LOCATIONS, planning_window
from mucon.llm.client import ChatMessage, LLMClient, LLMError
from mucon.schemas import (
    Constraint,
    ConstraintType,
    ExtractionResult,
    Message,
    Operator,
    Session,
)

DEFAULT_PROMPT = """You extract scheduling constraints from ONE chat message written by a \
member of a group that is planning an event together. Return every constraint the author \
states, as JSON:
{{"constraints": [{{"type": ..., "operator": ..., "value": ..., "strength": "hard"|"soft"}}]}}
Return {{"constraints": []}} if the message states no constraint.

Field rules:
- type: one of {types}
- operator: one of {operators}  (lte = "at most / before / under", gte = "at least / after")
- value formats by type:
  - date: ISO date "YYYY-MM-DD". Planning window: {calendar}
  - time: "HH:MM" (24h)
  - budget: number, TL per person
  - location: one of {locations}
  - diet: one of {diets}
  - capacity: integer number of people the venue must hold (use operator gte)
  - accessibility: true (wheelchair accessible)
  - activity: one of {activities}
- For "either X or Y" use operator "in" with a list value. For "not X" use "neq".
- If the author changes an earlier answer, extract only the NEW constraint.
- strength: "hard" for requirements, "soft" for mild preferences ("would be nice").

Message from {author}: "{text}"
"""


class ExtractionScore(BaseModel):
    """Kısıt çıkarıcının altın standarda göre başarımı (mesaj düzeyinde eşleşme)."""

    n_messages: int
    n_gold: int
    n_pred: int
    type_precision: float
    type_recall: float
    exact_precision: float  # tür + operatör + değer eşleşmesi
    exact_recall: float
    n_errors: int  # geçerli JSON alınamayan mesajlar


def _calendar(dates: list[str]) -> str:
    return ", ".join(f"{date.fromisoformat(d).strftime('%a %b %-d')}={d}" for d in dates)


def _norm_value(c: Constraint) -> object:
    v = c.value
    if isinstance(v, list):
        return tuple(sorted(str(x).lower() for x in v))
    if c.type in (ConstraintType.BUDGET, ConstraintType.CAPACITY):
        try:
            return float(v)
        except (TypeError, ValueError):
            return str(v).lower()
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return {"true": True, "false": False}.get(s, s)


def constraint_key(c: Constraint, *, exact: bool) -> tuple[object, ...]:
    """Eşleştirme anahtarı: yalnız tür ya da tür + operatör + normalize değer."""
    if not exact:
        return (c.source_message_id, c.type)
    return (c.source_message_id, c.type, c.operator, _norm_value(c))


class ConstraintExtractor:
    """Mesaj + oturum bağlamından yapılandırılmış kısıt çıkarır."""

    def __init__(
        self,
        llm: LLMClient,
        *,
        prompt_template: str | None = None,
        dates: list[str] | None = None,
        seed: int | None = None,
    ) -> None:
        self.llm = llm
        self.prompt_template = prompt_template or DEFAULT_PROMPT
        self.dates = dates or planning_window()
        self.seed = seed

    def build_prompt(self, message: Message, session: Session) -> str:
        names = {u.id: u.name for u in session.users}
        return self.prompt_template.format(
            types=", ".join(t.value for t in ConstraintType),
            operators=", ".join(o.value for o in Operator),
            calendar=_calendar(self.dates),
            locations=", ".join(LOCATIONS),
            diets=", ".join(DIETS),
            activities=", ".join(ACTIVITIES),
            author=names.get(message.user_id or "", message.user_id or "user"),
            text=message.text.replace('"', "'"),
        )

    def extract(self, message: Message, session: Session) -> list[Constraint]:
        """Tek bir kullanıcı mesajındaki kısıtları döndürür."""
        prompt = self.build_prompt(message, session)
        result = self.llm.structured(
            [ChatMessage(role="user", content=prompt)], ExtractionResult, seed=self.seed
        )
        return [
            Constraint(
                id=f"{message.id}-x{k + 1}",
                user_id=message.user_id or "",
                type=e.type,
                operator=e.operator,
                value=e.value,
                strength=e.strength,
                source_message_id=message.id,
                raw_text=message.text,
            )
            for k, e in enumerate(result.constraints)
        ]

    def extract_safe(self, message: Message, session: Session) -> list[Constraint] | None:
        """`extract` gibi; geçerli çıktı alınamazsa None (toplu değerlendirme için)."""
        try:
            return self.extract(message, session)
        except LLMError:
            return None


def score_extraction(
    gold: list[Constraint], pred: list[Constraint], *, n_messages: int, n_errors: int = 0
) -> ExtractionScore:
    """Mesaj düzeyinde çoklu küme eşleştirmesiyle P/R."""

    def pr(exact: bool) -> tuple[float, float]:
        g = Counter(constraint_key(c, exact=exact) for c in gold)
        p = Counter(constraint_key(c, exact=exact) for c in pred)
        tp = sum((g & p).values())
        return (tp / len(pred) if pred else 0.0, tp / len(gold) if gold else 0.0)

    tp_, tr_ = pr(False)
    ep, er = pr(True)
    return ExtractionScore(
        n_messages=n_messages,
        n_gold=len(gold),
        n_pred=len(pred),
        type_precision=tp_,
        type_recall=tr_,
        exact_precision=ep,
        exact_recall=er,
        n_errors=n_errors,
    )
