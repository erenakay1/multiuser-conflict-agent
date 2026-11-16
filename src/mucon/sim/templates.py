"""Kısıt → doğal dil mesaj şablonları (senaryo üreteci v0, LLM'siz).

Her (ConstraintType, Operator) için birkaç parafraz vardır; böylece dedektörler tek bir kalıbı
ezberleyemez. Mesajlar İngilizce'dir.
"""

from __future__ import annotations

import random
from datetime import date

from mucon.schemas import Constraint, ConstraintType, ConstraintValue, Operator

USER_NAMES: tuple[str, ...] = (
    "Ali", "Ayşe", "Deniz", "Elif", "Can", "Zeynep", "Mert", "Selin", "Emre", "Derya",
    "Kerem", "Ece", "Burak", "Naz", "Onur", "İrem",
)  # fmt: skip

PERSONAS: tuple[str, ...] = (
    "Works long weekday hours and prefers relaxed plans.",
    "Student on a tight budget.",
    "Organised planner who likes to decide early.",
    "Foodie who cares most about the venue.",
    "Lives far from the city centre and hates long commutes.",
    "Easy-going, but has a few firm requirements.",
    "Parent with an early schedule.",
    "Night owl who enjoys late evenings.",
)

OPENERS: tuple[str, ...] = ("", "", "", "Hi all! ", "Quick note: ", "Okay! ", "Hey everyone. ")
REVISION_PREFIXES: tuple[str, ...] = (
    "Actually, change of plans: ",
    "Sorry, scratch what I said earlier. ",
    "Update from my side: ",
    "Wait, I need to change my answer. ",
)

DIET_PHRASES: dict[str, str] = {
    "vegan": "vegan",
    "vegetarian": "vegetarian",
    "halal": "halal",
    "gluten_free": "gluten-free",
}
ACTIVITY_PHRASES: dict[str, str] = {
    "cafe": "a cosy cafe",
    "dinner": "a dinner restaurant",
    "steakhouse": "a steakhouse",
    "fine_dining": "a fine-dining restaurant",
    "bowling": "bowling",
    "karaoke": "karaoke",
    "escape_room": "an escape room",
    "rooftop_bar": "a rooftop bar",
    "cinema": "the cinema",
}

T = ConstraintType
Op = Operator
TEMPLATES: dict[tuple[ConstraintType, Operator], tuple[str, ...]] = {
    (T.DATE, Op.EQ): (
        "Let's do it on {v}.",
        "{V} works best for me.",
        "Can we plan it for {v}?",
        "I'm only free on {v}.",
    ),
    (T.DATE, Op.NEQ): ("I can't make it on {v}.", "Anything but {v} for me, I'm busy that day."),
    (T.DATE, Op.IN): ("Either {v} works for me.", "I could do {v}."),
    (T.TIME, Op.EQ): ("Let's start at {v}.", "{V} would be the perfect start time."),
    (T.TIME, Op.GTE): (
        "I can't come before {v}.",
        "Let's not start earlier than {v}, I work until then.",
    ),
    (T.TIME, Op.LTE): (
        "It should start by {v} at the latest.",
        "I need to be home early, so no later than {v} please.",
    ),
    (T.BUDGET, Op.LTE): (
        "I don't want to spend more than {v} TL per person.",
        "Let's keep it under {v} TL per head.",
        "My budget is {v} TL max.",
    ),
    (T.BUDGET, Op.GTE): (
        "I'd rather go somewhere nicer, at least {v} TL per person.",
        "Let's not go cheap this time, I'm fine with {v} TL or more per head.",
    ),
    (T.LOCATION, Op.EQ): ("It should be in {v}.", "Somewhere in {v} would be ideal."),
    (T.LOCATION, Op.NEQ): ("Not {v} please, it's too far for me.", "Anywhere except {v}."),
    (T.DIET, Op.EQ): (
        "I need a place with {v} options.",
        "I eat {v}, so the menu has to have {v} food.",
    ),
    (T.CAPACITY, Op.GTE): (
        "We'll be around {v} people, so the place needs room for {v}.",
        "Make sure the venue fits at least {v} of us.",
    ),
    (T.ACCESSIBILITY, Op.EQ): (
        "The venue must be wheelchair accessible.",
        "My cousin is joining and uses a wheelchair, so it has to be accessible.",
    ),
    (T.ACTIVITY, Op.EQ): (
        "How about {v}?",
        "I really want to go to {v}.",
        "I vote for {v}.",
    ),
}


def _fmt_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.strftime('%A')}, {d.strftime('%b')} {d.day}"


def format_value(ctype: ConstraintType, value: ConstraintValue) -> str:
    """Kısıt değerini mesaj içinde okunacak hale getirir."""
    if isinstance(value, list):
        parts = [format_value(ctype, v) for v in value]
        return " or ".join(parts)
    if ctype == T.DATE:
        return _fmt_date(str(value))
    if ctype == T.DIET:
        return DIET_PHRASES.get(str(value), str(value))
    if ctype == T.ACTIVITY:
        return ACTIVITY_PHRASES.get(str(value), str(value))
    if ctype == T.BUDGET and isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def render(constraint: Constraint, rng: random.Random, *, revision: bool = False) -> str:
    """Bir kısıtı tek cümlelik kullanıcı mesajına çevirir."""
    key = (constraint.type, constraint.operator)
    if key not in TEMPLATES:
        raise KeyError(f"Şablon yok: {key}")
    text = rng.choice(TEMPLATES[key])
    v = format_value(constraint.type, constraint.value)
    text = text.replace("{V}", v[:1].upper() + v[1:]).replace("{v}", v)
    prefix = rng.choice(REVISION_PREFIXES) if revision else rng.choice(OPENERS)
    return prefix + text
