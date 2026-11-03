"""İstatistiksel karşılaştırma: eşleştirilmiş Wilcoxon işaretli sıra testi."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import pandas as pd
from pydantic import BaseModel


class WilcoxonResult(BaseModel):
    statistic: float
    p_value: float
    n: int
    effect_size: float | None = None  # r = Z / sqrt(n)


def wilcoxon_compare(
    a: Sequence[float],
    b: Sequence[float],
    *,
    alternative: Literal["two-sided", "less", "greater"] = "two-sided",
) -> WilcoxonResult:
    """Aynı senaryolar üzerindeki iki stratejinin eşleştirilmiş skorlarını karşılaştırır."""
    # TODO(H8): scipy.stats.wilcoxon
    raise NotImplementedError


def pairwise_wilcoxon(
    df: pd.DataFrame,
    metric: str,
    *,
    by: str = "strategy",
    pair_on: str = "scenario_id",
    correction: Literal["holm", "bonferroni", "none"] = "holm",
) -> pd.DataFrame:
    """Tüm strateji çiftleri için Wilcoxon + çoklu karşılaştırma düzeltmesi."""
    # TODO(H8): Wilcoxon, çoklu karşılaştırma düzeltmesi
    raise NotImplementedError
