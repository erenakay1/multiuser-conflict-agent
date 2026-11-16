"""Gizli tercihli kullanıcılardan oluşan etkinlik planlama senaryoları üretir.

v0 (şablon tabanlı, LLM'siz) yöntemi:
1. Bir **hedef plan** (mekan + tarih + saat) seçilir. Arka plan kısıtlarının hepsi bu hedefle
   sağlanır, bu yüzden aralarında çakışma olmaz.
2. Senaryo türüne göre tek bir kısıt çifti eklenir:
   - çakışma (direct / range / indirect / revision): çiftin bir tarafı hedefle uyumlu, diğeri değil;
   - near-miss (çakışma yok): aynı öznitelikte ama uyumlu iki kısıt (dedektörler için zor negatif);
   - none: ek çift yok.
3. Her kısıt tek bir kullanıcı mesajına çevrilir (`sim/templates.py`).
4. Altın etiketler tüm kullanıcı mesajı çiftleri için üretilir (annotator="generator") ve
   ortam veritabanıyla doğrulanır: çakışan çift birlikte sağlanamaz, diğer tüm çiftler sağlanabilir.
   Doğrulama tutmazsa senaryo yeniden örneklenir.
"""

from __future__ import annotations

import itertools
import json
import math
import random
from collections.abc import Callable
from pathlib import Path

from mucon.env.event_planning import (
    ACTIVITIES,
    LOCATIONS,
    VenueDB,
    find_feasible_plan,
    planning_window,
    satisfies,
)
from mucon.llm.client import LLMClient
from mucon.schemas import (
    ConflictLabel,
    ConflictType,
    Constraint,
    ConstraintType,
    ConstraintValue,
    EventPlan,
    Message,
    MessageRole,
    Operator,
    Scenario,
    User,
    UserPersona,
    Venue,
)
from mucon.sim.templates import PERSONAS, USER_NAMES, render

T = ConstraintType
Op = Operator
GENERATOR_ANNOTATOR = "generator"
NEAR_MISS = "near_miss"
NONE = "none"
MAX_ATTEMPTS = 200

# INDIRECT kuralları: (A tarafı, B tarafı). Ortam sağduyu kurallarıyla tutarlı olmalı
# (bkz. env/event_planning.py modül açıklaması).
_Spec = tuple[ConstraintType, Operator, ConstraintValue]
INDIRECT_RULES: tuple[tuple[_Spec, _Spec], ...] = (
    ((T.DIET, Op.EQ, "vegan"), (T.ACTIVITY, Op.EQ, "steakhouse")),
    ((T.BUDGET, Op.LTE, 400.0), (T.ACTIVITY, Op.EQ, "fine_dining")),
    ((T.ACCESSIBILITY, Op.EQ, True), (T.ACTIVITY, Op.EQ, "rooftop_bar")),
    ((T.CAPACITY, Op.GTE, 15), (T.ACTIVITY, Op.EQ, "escape_room")),
)


def _round_up(x: float, step: int = 100) -> float:
    return float(math.ceil(x / step) * step)


def _hour(t: str) -> int:
    return int(t[:2])


def _slot(h: int) -> str:
    return f"{h:02d}:00"


class _Draft:
    """Tek senaryonun üretim taslağı: (kullanıcı indeksi, kısıt, revizyon mu) listesi."""

    def __init__(self, conflict: bool) -> None:
        self.conflict = conflict  # eklenen çift çakışıyor mu (near-miss: hayır)
        self.items: list[tuple[int, Constraint, bool]] = []
        self.pair: tuple[int, int] | None = None  # eklenen çiftin items indeksleri
        self.superseded: set[int] = set()  # revizyonla geçersizleşen items indeksleri

    def add(self, user: int, c: Constraint, *, revision: bool = False) -> int:
        self.items.append((user, c, revision))
        return len(self.items) - 1


def _c(ctype: ConstraintType, op: Operator, value: ConstraintValue) -> Constraint:
    """Geçici id'li kısıt; kalıcı id'ler senaryo kurulurken verilir."""
    return Constraint(id="tmp", user_id="tmp", type=ctype, operator=op, value=value)


class ScenarioGenerator:
    """Seed'li senaryo üreteci. Çakışma oranı ve kullanıcı sayısı ayarlanabilir."""

    def __init__(
        self,
        seed: int,
        *,
        db: VenueDB,
        llm: LLMClient | None = None,
        n_users_range: tuple[int, int] = (2, 4),
        conflict_rate: float = 0.5,
        near_miss_rate: float = 0.5,
        dates: list[str] | None = None,
    ) -> None:
        """`near_miss_rate`: çakışmasız senaryoların ne kadarına zor negatif çift eklenir.

        `llm` v0'da kullanılmaz; ileride mesajların parafrazı için ayrılmıştır.
        """
        if not 0.0 <= conflict_rate <= 1.0:
            raise ValueError("conflict_rate [0, 1] aralığında olmalı")
        self.seed = seed
        self.db = db
        self.llm = llm
        self.n_users_range = n_users_range
        self.conflict_rate = conflict_rate
        self.near_miss_rate = near_miss_rate
        self.dates = dates or planning_window()

    # ------------------------------------------------------------------ public

    def generate(self, n: int) -> list[Scenario]:
        """`n` senaryo üretir. Çakışma türleri dengeli dağıtılır."""
        rng = random.Random(self.seed)
        kinds = self._plan_kinds(n, rng)
        scenarios: list[Scenario] = []
        for i, kind in enumerate(kinds):
            sub_seed = rng.randrange(2**31)
            scenarios.append(self._generate_one(f"sc-{i + 1:04d}", kind, sub_seed))
        return scenarios

    @staticmethod
    def save(scenarios: list[Scenario], out_dir: Path) -> list[Path]:
        """Her senaryoyu `<out_dir>/<id>.json` olarak kaydeder."""
        out_dir.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []
        for sc in scenarios:
            path = out_dir / f"{sc.id}.json"
            path.write_text(sc.model_dump_json(indent=2) + "\n", encoding="utf-8")
            paths.append(path)
        return paths

    @staticmethod
    def load(in_dir: Path) -> list[Scenario]:
        """Bir klasördeki tüm senaryoları (id sırasıyla) yükler."""
        return [
            Scenario.model_validate(json.loads(p.read_text(encoding="utf-8")))
            for p in sorted(in_dir.glob("*.json"))
        ]

    # ------------------------------------------------------------------ plan

    def _plan_kinds(self, n: int, rng: random.Random) -> list[str]:
        n_conflict = round(n * self.conflict_rate)
        types = list(ConflictType)
        kinds = [types[i % len(types)].value for i in range(n_conflict)]
        n_free = n - n_conflict
        n_near = round(n_free * self.near_miss_rate)
        kinds += [NEAR_MISS] * n_near + [NONE] * (n_free - n_near)
        rng.shuffle(kinds)
        return kinds

    def _generate_one(self, sid: str, kind: str, seed: int) -> Scenario:
        rng = random.Random(seed)
        for _ in range(MAX_ATTEMPTS):
            draft = self._draft(kind, rng)
            if draft is not None and self._valid(draft):
                return self._build(sid, kind, seed, draft, rng)
        raise RuntimeError(f"{sid}: {MAX_ATTEMPTS} denemede geçerli '{kind}' senaryosu üretilemedi")

    # ------------------------------------------------------------------ draft

    def _draft(self, kind: str, rng: random.Random) -> _Draft | None:
        n_users = rng.randint(*self.n_users_range)
        draft = _Draft(conflict=kind in {t.value for t in ConflictType})

        if kind == ConflictType.INDIRECT:
            rule = rng.choice(INDIRECT_RULES)
            sat_side = rng.randrange(2)  # hedefin sağladığı taraf
            sat_c = _c(*rule[sat_side])
            target = self._pick_target(rng, lambda p: satisfies(p, sat_c, self.db))
            if target is None:
                return None
            venue, plan = target
            a: Constraint | None = _c(*rule[0])
            b: Constraint | None = _c(*rule[1])
            used = {rule[0][0], rule[1][0]}
        else:
            target = self._pick_target(rng)
            if target is None:
                return None
            venue, plan = target
            pair = self._pair(kind, venue, plan, rng)
            if pair is None and kind != NONE:
                return None
            a, b = pair if pair else (None, None)
            used = {a.type} if a is not None else set()

        # Çift: farklı kullanıcılar (revizyonda aynı kullanıcı, eski talimat önce)
        if a is not None and b is not None:
            ua = rng.randrange(n_users)
            if kind == ConflictType.REVISION:
                old_i = draft.add(ua, a)
                new_i = draft.add(ua, b, revision=True)
                draft.pair = (old_i, new_i)
                draft.superseded.add(old_i)
            else:
                ub = rng.choice([u for u in range(n_users) if u != ua])
                draft.pair = (draft.add(ua, a), draft.add(ub, b))

        # Arka plan: hedefle sağlanan, çiftte kullanılmayan özniteliklerden
        bg_pool = [c for c in self._background(venue, plan, rng) if c.type not in used]
        rng.shuffle(bg_pool)
        users_with_msg = {u for u, _, _ in draft.items}
        need = [u for u in range(n_users) if u not in users_with_msg]
        n_bg = max(len(need), rng.randint(n_users - 1, n_users + 1))
        if n_bg > len(bg_pool):
            return None
        for k, c in enumerate(bg_pool[:n_bg]):
            user = need[k] if k < len(need) else rng.randrange(n_users)
            draft.add(user, c)
        return draft

    def _pick_target(
        self, rng: random.Random, accept: Callable[[EventPlan], bool] | None = None
    ) -> tuple[Venue, EventPlan] | None:
        venues = [v for v in self.db.venues if v.available_dates]
        rng.shuffle(venues)
        for v in venues:
            plan = EventPlan(
                venue_id=v.id,
                date=rng.choice(v.available_dates),
                start_time=_slot(rng.randint(12, 21)),
                budget_per_person=v.price_per_person,
            )
            if accept is None or accept(plan):
                return v, plan
        return None

    def _background(self, v: Venue, plan: EventPlan, rng: random.Random) -> list[Constraint]:
        assert plan.date is not None and plan.start_time is not None
        h = _hour(plan.start_time)
        out = [
            _c(T.DATE, Op.EQ, plan.date),
            _c(T.BUDGET, Op.LTE, _round_up(v.price_per_person) + 100 * rng.randint(0, 2)),
            _c(T.LOCATION, Op.EQ, v.location),
            _c(T.ACTIVITY, Op.EQ, v.tags[0]),
            _c(T.CAPACITY, Op.GTE, rng.randint(min(4, v.capacity), min(12, v.capacity))),
            rng.choice(
                [
                    _c(T.TIME, Op.GTE, _slot(max(10, h - rng.randint(0, 2)))),
                    _c(T.TIME, Op.LTE, _slot(min(23, h + rng.randint(0, 2)))),
                ]
            ),
        ]
        if v.diet_options:
            out.append(_c(T.DIET, Op.EQ, rng.choice(v.diet_options)))
        if v.accessible:
            out.append(_c(T.ACCESSIBILITY, Op.EQ, True))
        return out

    def _pair(
        self, kind: str, v: Venue, plan: EventPlan, rng: random.Random
    ) -> tuple[Constraint, Constraint] | None:
        """(A, B) çifti; A daima hedefle sağlanır. INDIRECT burada değil, `_draft` içinde."""
        assert plan.date is not None and plan.start_time is not None
        h = _hour(plan.start_time)
        other_date = rng.choice([d for d in self.dates if d != plan.date])
        other_loc = rng.choice([loc for loc in LOCATIONS if loc != v.location])
        other_act = rng.choice([a for a in ACTIVITIES if a != v.tags[0]])
        other_time = _slot(rng.choice([x for x in range(12, 23) if x != h]))

        if kind == ConflictType.DIRECT:
            options = [
                (_c(T.DATE, Op.EQ, plan.date), _c(T.DATE, Op.EQ, other_date)),
                (_c(T.DATE, Op.EQ, plan.date), _c(T.DATE, Op.NEQ, plan.date)),
                (_c(T.LOCATION, Op.EQ, v.location), _c(T.LOCATION, Op.EQ, other_loc)),
                (_c(T.LOCATION, Op.EQ, v.location), _c(T.LOCATION, Op.NEQ, v.location)),
                (_c(T.ACTIVITY, Op.EQ, v.tags[0]), _c(T.ACTIVITY, Op.EQ, other_act)),
                (_c(T.TIME, Op.EQ, plan.start_time), _c(T.TIME, Op.EQ, other_time)),
            ]
            return rng.choice(options)
        if kind == ConflictType.RANGE:
            if rng.random() < 0.5:  # bütçe: A ≤ x, B ≥ y (y > x)
                x = _round_up(v.price_per_person) + 100 * rng.randint(0, 2)
                return _c(T.BUDGET, Op.LTE, x), _c(T.BUDGET, Op.GTE, x + 100 * rng.randint(3, 6))
            lo = max(12, h - rng.randint(0, 2))  # saat: A ≥ lo, B ≤ lo - k
            if lo - 2 < 10:
                return None
            return _c(T.TIME, Op.GTE, _slot(lo)), _c(T.TIME, Op.LTE, _slot(lo - rng.randint(2, 3)))
        if kind == ConflictType.REVISION:  # (eski, yeni); yeni hedefle sağlanır
            options = [
                (_c(T.DATE, Op.EQ, other_date), _c(T.DATE, Op.EQ, plan.date)),
                (_c(T.LOCATION, Op.EQ, other_loc), _c(T.LOCATION, Op.EQ, v.location)),
                (_c(T.TIME, Op.EQ, other_time), _c(T.TIME, Op.EQ, plan.start_time)),
            ]
            old, new = rng.choice(options)
            return old, new
        if kind == NEAR_MISS:
            x = _round_up(v.price_per_person)
            options = [
                (_c(T.BUDGET, Op.LTE, x), _c(T.BUDGET, Op.LTE, x + 100 * rng.randint(2, 5))),
                (_c(T.DATE, Op.EQ, plan.date), _c(T.DATE, Op.IN, sorted([plan.date, other_date]))),
                (_c(T.DATE, Op.EQ, plan.date), _c(T.DATE, Op.NEQ, other_date)),
                (_c(T.LOCATION, Op.EQ, v.location), _c(T.LOCATION, Op.NEQ, other_loc)),
                (
                    _c(T.TIME, Op.GTE, _slot(max(10, h - 1))),
                    _c(T.TIME, Op.LTE, _slot(min(23, h + 1))),
                ),
            ]
            return rng.choice(options)
        return None  # NONE

    # ------------------------------------------------------------------ validate

    def _feasible(self, cs: list[Constraint]) -> bool:
        return find_feasible_plan(cs, self.db) is not None

    def _valid(self, draft: _Draft) -> bool:
        """Etiketlerin ortamla tutarlı olduğunu doğrular (bkz. modül açıklaması)."""
        cs = [c for _, c, _ in draft.items]
        if any(not self._feasible([c]) for c in cs):
            return False
        for i, j in itertools.combinations(range(len(cs)), 2):
            should_conflict = draft.conflict and draft.pair == (i, j)
            if self._feasible([cs[i], cs[j]]) == should_conflict:
                return False  # çakışan çift sağlanabiliyor ya da başka bir çift sağlanamıyor
        if not draft.conflict or draft.superseded:  # nihai tercihler birlikte sağlanabilmeli
            return self._feasible([c for k, c in enumerate(cs) if k not in draft.superseded])
        return True

    # ------------------------------------------------------------------ build

    def _build(self, sid: str, kind: str, seed: int, draft: _Draft, rng: random.Random) -> Scenario:
        n_users = max(u for u, _, _ in draft.items) + 1
        names = rng.sample(USER_NAMES, n_users)
        users = [User(id=f"u{k + 1}", name=names[k]) for k in range(n_users)]

        # Mesaj sırası: karışık; revizyonda eski talimat yeniden önce gelir
        order = list(range(len(draft.items)))
        rng.shuffle(order)
        if draft.superseded and draft.pair is not None:
            old_i, new_i = draft.pair
            if order.index(old_i) > order.index(new_i):
                a, b = order.index(old_i), order.index(new_i)
                order[a], order[b] = order[b], order[a]

        messages: list[Message] = []
        gold: list[Constraint] = []
        item_to_msg: dict[int, str] = {}
        for turn, idx in enumerate(order):
            u, c, revision = draft.items[idx]
            mid, cid = f"m{turn + 1}", f"c{turn + 1}"
            text = render(c, rng, revision=revision)
            messages.append(
                Message(id=mid, role=MessageRole.USER, user_id=users[u].id, turn=turn, text=text)
            )
            gold.append(
                c.model_copy(
                    update={
                        "id": cid,
                        "user_id": users[u].id,
                        "source_message_id": mid,
                        "raw_text": text,
                    }
                )
            )
            item_to_msg[idx] = mid

        superseded_ids = {item_to_msg[i] for i in draft.superseded}
        personas = [
            UserPersona(
                user=user,
                persona=rng.choice(PERSONAS),
                hidden_preferences=[
                    g
                    for g in gold
                    if g.user_id == user.id and g.source_message_id not in superseded_ids
                ],
            )
            for user in users
        ]

        pair_msgs = (
            {item_to_msg[draft.pair[0]], item_to_msg[draft.pair[1]]} if draft.pair else set()
        )
        labels: list[ConflictLabel] = []
        for m1, m2 in itertools.combinations([m.id for m in messages], 2):
            hit = draft.conflict and {m1, m2} == pair_msgs
            labels.append(
                ConflictLabel(
                    scenario_id=sid,
                    message_ids=[m1, m2],
                    has_conflict=hit,
                    conflict_type=ConflictType(kind) if hit else None,
                    annotator=GENERATOR_ANNOTATOR,
                )
            )

        return Scenario(
            id=sid,
            description=f"{n_users} users, {len(messages)} messages; generator kind={kind}",
            personas=personas,
            scripted_messages=messages,
            gold_constraints=gold,
            gold_labels=labels,
            seed=seed,
        )
