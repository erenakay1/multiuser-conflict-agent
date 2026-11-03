"""Muses-Bench JSONL dosyalarından kullanıcı sayısına göre tabakalı, seed'li alt küme üretir.

Çıktı, Ollama'yı 16 paralel istekle boğmamak için `chunk` satırlık parçalara bölünür.

Kullanım:
    uv run python scripts/make_muses_subset.py IN.jsonl OUT_DIR --per-group 5 --seed 42 --chunk 8
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def n_users(row: dict) -> int:
    meta = row.get("meta") or {}
    return int(meta.get("num_users") or len(row["users"]))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("out_dir", type=Path)
    p.add_argument("--per-group", type=int, default=5)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--chunk", type=int, default=8)
    args = p.parse_args()

    groups: dict[int, list[str]] = defaultdict(list)
    for line in args.input.read_text().splitlines():
        if line.strip():
            groups[n_users(json.loads(line))].append(line)

    rng = random.Random(args.seed)
    picked = [
        ln
        for k in sorted(groups)
        for ln in rng.sample(groups[k], min(args.per_group, len(groups[k])))
    ]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.input.stem
    for i in range(0, len(picked), args.chunk):
        out = args.out_dir / f"{stem}_part{i // args.chunk:02d}.jsonl"
        out.write_text("\n".join(picked[i : i + args.chunk]) + "\n")
    print(f"{stem}: {len(picked)} örnek, {sorted(groups)} kullanıcı grupları -> {args.out_dir}")


if __name__ == "__main__":
    main()
