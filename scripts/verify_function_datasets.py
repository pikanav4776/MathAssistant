"""Verify function training/testing dataset distribution constraints."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from function_datasets import (  # noqa: E402
    FUNCTION_TESTING_DATASET,
    FUNCTION_TOPICS,
    FUNCTION_TRAINING_DATASET,
)

DIFFICULTIES = ("easy", "medium", "hard")


def _check_split(label: str, dataset: list[dict]) -> bool:
    ok = True
    print(f"\n{label} ({len(dataset)} problems)")
    by_topic = Counter(problem["topic"] for problem in dataset)
    for topic in FUNCTION_TOPICS:
        items = [problem for problem in dataset if problem["topic"] == topic]
        counts = Counter(problem["difficulty"] for problem in items)
        print(
            f"  {topic:<24} total={len(items):>2}  "
            f"easy={counts['easy']} medium={counts['medium']} hard={counts['hard']}"
        )
        if len(items) != 10:
            ok = False
        if counts["easy"] != 3 or counts["medium"] != 3 or counts["hard"] != 4:
            ok = False
    print(f"  topics present: {sorted(by_topic)}")
    return ok


def main() -> int:
    training_ok = _check_split("Training set", FUNCTION_TRAINING_DATASET)
    testing_ok = _check_split("Testing set", FUNCTION_TESTING_DATASET)
    if training_ok and testing_ok:
        print("\nFunction dataset verification passed.")
        return 0
    print("\nFunction dataset verification failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
