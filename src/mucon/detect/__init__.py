"""Çakışma dedektörleri."""

from mucon.detect.base import ConflictDetector
from mucon.detect.deberta import DebertaNLIDetector
from mucon.detect.llm_zero_shot import LLMZeroShotDetector
from mucon.detect.rule_based import RuleBasedDetector

DETECTORS: dict[str, type[ConflictDetector]] = {
    RuleBasedDetector.name: RuleBasedDetector,
    LLMZeroShotDetector.name: LLMZeroShotDetector,
    DebertaNLIDetector.name: DebertaNLIDetector,
}

__all__ = [
    "DETECTORS",
    "ConflictDetector",
    "DebertaNLIDetector",
    "LLMZeroShotDetector",
    "RuleBasedDetector",
]
