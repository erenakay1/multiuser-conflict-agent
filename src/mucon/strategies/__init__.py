"""Koordinasyon stratejileri (S0–S4)."""

from mucon.strategies.base import CoordinationStrategy
from mucon.strategies.s0_naive import NaiveStrategy
from mucon.strategies.s1_last_wins import LastWinsStrategy
from mucon.strategies.s2_hierarchy import HierarchyStrategy
from mucon.strategies.s3_compromise import CompromiseStrategy
from mucon.strategies.s4_group_vote import GroupVoteStrategy

STRATEGIES: dict[str, type[CoordinationStrategy]] = {
    NaiveStrategy.name: NaiveStrategy,
    LastWinsStrategy.name: LastWinsStrategy,
    HierarchyStrategy.name: HierarchyStrategy,
    CompromiseStrategy.name: CompromiseStrategy,
    GroupVoteStrategy.name: GroupVoteStrategy,
}

__all__ = [
    "STRATEGIES",
    "CompromiseStrategy",
    "CoordinationStrategy",
    "GroupVoteStrategy",
    "HierarchyStrategy",
    "LastWinsStrategy",
    "NaiveStrategy",
]
