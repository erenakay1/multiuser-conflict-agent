"""RQ2 — Stratejilerin görev başarısı, adalet ve verimlilik açısından karşılaştırılması.

Kullanım: uv run python experiments/run_strategy_comparison.py configs/experiments/example.yaml
"""

from __future__ import annotations

import sys
from pathlib import Path


def main(config_path: Path) -> None:
    """runner.run_experiment'ı koşar ve Wilcoxon karşılaştırmalarını üretir."""
    # TODO(H8): tam strateji karşılaştırma deneyi
    raise NotImplementedError


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("configs/experiments/example.yaml"))
