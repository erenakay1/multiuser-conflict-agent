"""RQ1 — Çakışma dedektörlerinin etiketli veride P/R/F1 değerlendirmesi.

Kullanım: uv run python experiments/run_detector_eval.py configs/experiments/example.yaml
"""

from __future__ import annotations

import sys
from pathlib import Path


def main(config_path: Path) -> None:
    """Etiketli senaryoları yükler, her dedektörü koşar, P/R/F1'i results/ altına yazar."""
    # TODO(H5): dedektör değerlendirme deneyi
    raise NotImplementedError


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("configs/experiments/example.yaml"))
