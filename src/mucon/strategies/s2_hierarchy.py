"""S2 — Yetki hiyerarşisi (baseline; Fan et al. 2026, Yang et al. 2026).

Çakışmada `User.rank` değeri yüksek olan kullanıcının kısıtı kazanır.
Eşit yetkide eşitlik bozma kuralı gerekir (ör. sabit kullanıcı sırası).
"""

from __future__ import annotations

from typing import ClassVar

from mucon.schemas import Action, Conflict, Session
from mucon.strategies.base import CoordinationStrategy


class HierarchyStrategy(CoordinationStrategy):
    name: ClassVar[str] = "s2_hierarchy"

    def resolve(self, session: Session, conflicts: list[Conflict]) -> Action:
        # TODO(H4): S2 — rank'e göre APPLY_OVERRIDE
        raise NotImplementedError
