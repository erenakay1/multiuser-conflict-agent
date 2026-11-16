"""İnsan etiketleme yardımcıları ve etiketleyiciler arası uyum (Cohen's κ).

Etiket dosyası: `data/labels/<annotator>.jsonl`, satır başına bir `ConflictLabel`.
Etiketleme girdisi biçimi: `"1-3 direct, 2-5 ind"` → 1. ve 3. mesaj DIRECT, 2. ve 5. INDIRECT.
Tür adları benzersiz bir önekle kısaltılabilir (dir, ra, ind, rev). Boş girdi = hiç çakışma yok.
Listelenmeyen tüm mesaj çiftleri `has_conflict=False` olarak kaydedilir.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

from pydantic import BaseModel
from sklearn.metrics import cohen_kappa_score

from mucon.schemas import ConflictLabel, ConflictType, Scenario

NO_CONFLICT = "none"


def parse_conflict_type(token: str) -> ConflictType:
    """Tür adını veya benzersiz önekini çözer ("ind" → INDIRECT)."""
    token = token.strip().lower()
    matches = [t for t in ConflictType if t.value.startswith(token)] if token else []
    if len(matches) != 1:
        options = ", ".join(t.value for t in ConflictType)
        raise ValueError(f"'{token}' tanınmadı veya belirsiz (seçenekler: {options})")
    return matches[0]


def parse_annotation(text: str, n_messages: int) -> dict[frozenset[int], ConflictType]:
    """Etiketleme girdisini {mesaj numarası çifti (1'den başlar): tür} sözlüğüne çevirir."""
    result: dict[frozenset[int], ConflictType] = {}
    for part in filter(None, (p.strip() for p in text.split(","))):
        try:
            pair_str, type_str = part.split(maxsplit=1)
            a_str, b_str = pair_str.split("-")
            a, b = int(a_str), int(b_str)
        except ValueError as e:
            raise ValueError(f"'{part}' biçimi hatalı; örnek: '1-3 direct'") from e
        if a == b or not (1 <= a <= n_messages and 1 <= b <= n_messages):
            raise ValueError(
                f"'{part}': mesaj numaraları 1..{n_messages} arasında ve farklı olmalı"
            )
        key = frozenset((a, b))
        if key in result:
            raise ValueError(f"'{part}': bu çift iki kez etiketlendi")
        result[key] = parse_conflict_type(type_str)
    return result


def labels_for_scenario(
    scenario: Scenario,
    conflicts: dict[frozenset[int], ConflictType],
    annotator: str,
    notes: str = "",
) -> list[ConflictLabel]:
    """Senaryodaki tüm kullanıcı mesajı çiftleri için etiket üretir."""
    msgs = scenario.user_messages()
    labels: list[ConflictLabel] = []
    for (i, m1), (j, m2) in itertools.combinations(enumerate(msgs, start=1), 2):
        ctype = conflicts.get(frozenset((i, j)))
        labels.append(
            ConflictLabel(
                scenario_id=scenario.id,
                message_ids=[m1.id, m2.id],
                has_conflict=ctype is not None,
                conflict_type=ctype,
                annotator=annotator,
                notes=notes if ctype is not None else "",
            )
        )
    return labels


def load_labels(path: Path) -> list[ConflictLabel]:
    if not path.exists():
        return []
    return [
        ConflictLabel.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def append_labels(path: Path, labels: list[ConflictLabel]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for label in labels:
            f.write(json.dumps(label.model_dump(mode="json"), ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Uyum
# ---------------------------------------------------------------------------

PairKey = tuple[str, frozenset[str]]


def _index(labels: list[ConflictLabel]) -> dict[PairKey, str]:
    return {
        (lb.scenario_id, frozenset(lb.message_ids)): (
            lb.conflict_type.value if lb.conflict_type else NO_CONFLICT
        )
        for lb in labels
    }


class Disagreement(BaseModel):
    scenario_id: str
    message_ids: list[str]
    a: str
    b: str


class AgreementReport(BaseModel):
    n_pairs: int
    n_scenarios: int
    binary_accuracy: float
    binary_kappa: float
    type_accuracy: float  # 5 sınıf: none + 4 tür
    type_kappa: float
    n_conflicts_a: int
    n_conflicts_b: int
    disagreements: list[Disagreement]


def agreement(a: list[ConflictLabel], b: list[ConflictLabel]) -> AgreementReport:
    """İki etiket kümesinin ortak mesaj çiftleri üzerindeki uyumu."""
    ia, ib = _index(a), _index(b)
    keys = sorted(set(ia) & set(ib), key=lambda k: (k[0], sorted(k[1])))
    if not keys:
        raise ValueError("Ortak etiketlenmiş mesaj çifti yok")
    ya, yb = [ia[k] for k in keys], [ib[k] for k in keys]
    ba = [y != NO_CONFLICT for y in ya]
    bb = [y != NO_CONFLICT for y in yb]

    def kappa(x: list[object], y: list[object]) -> float:
        k = cohen_kappa_score(x, y)
        return 1.0 if k != k else float(k)  # tek sınıf + tam uyum → NaN; 1 kabul edilir

    return AgreementReport(
        n_pairs=len(keys),
        n_scenarios=len({k[0] for k in keys}),
        binary_accuracy=sum(x == y for x, y in zip(ba, bb, strict=True)) / len(keys),
        binary_kappa=kappa(list(ba), list(bb)),
        type_accuracy=sum(x == y for x, y in zip(ya, yb, strict=True)) / len(keys),
        type_kappa=kappa(list(ya), list(yb)),
        n_conflicts_a=sum(ba),
        n_conflicts_b=sum(bb),
        disagreements=[
            Disagreement(scenario_id=k[0], message_ids=sorted(k[1]), a=x, b=y)
            for k, x, y in zip(keys, ya, yb, strict=True)
            if x != y
        ],
    )
