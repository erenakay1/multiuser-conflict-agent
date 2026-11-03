"""Muses-Bench `run.py`'yi değiştirmeden çalıştırır ve her LLM çağrısının token/maliyetini kaydeder.

Muses-Bench kullanım bilgisi tutmadığı için litellm success callback'i ile her çağrı
`USAGE_LOG` (JSONL) dosyasına yazılır. Muses-Bench'in kendi venv'iyle çalıştırılmalıdır.

Kullanım (external/Muses-Bench içinden):
    USAGE_LOG=/abs/usage.jsonl .venv/bin/python ../../scripts/muses_run_with_usage.py <run.py args>
"""

from __future__ import annotations

import json
import os
import runpy
import sys
import threading
import time
from pathlib import Path

import litellm

sys.path.insert(0, os.getcwd())
import muses_bench.utils.env_loader  # noqa: F401  (muses_bench/.env -> os.environ; run.py yüklemiyor)

_lock = threading.Lock()
_log = Path(os.environ["USAGE_LOG"])


def _record(kwargs: dict, response: object, start: object, end: object) -> None:
    usage = getattr(response, "usage", None)
    row = {
        "ts": time.time(),
        "model": kwargs.get("model"),
        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
        "completion_tokens": getattr(usage, "completion_tokens", 0),
        "cost_usd": kwargs.get("response_cost") or 0.0,
    }
    with _lock, _log.open("a") as f:
        f.write(json.dumps(row) + "\n")


litellm.success_callback = [_record]

sys.argv = ["run.py", *sys.argv[1:]]
runpy.run_path("run.py", run_name="__main__")
