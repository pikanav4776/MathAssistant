"""Verify evaluation dataset distribution constraints."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from evaluation_dataset import EVALUATION_DATASET  # noqa: E402

ERROR_TYPES = ("distribution_error", "sign_error", "arithmetic_error")
DIFFICULTIES = ("easy", "medium", "hard")
TOPICS = ("distribution", "simplification", "double_expansion", "linear_steps")


def _pct(count: int, total: int) -> int:
    if total == 0:
        return 0
    return round(count * 100 / total)


def main() -> int:
    total_problems = len(EVALUATION_DATASET)
    by_difficulty = Counter(p["difficulty"] for p in EVALUATION_DATASET)
    by_topic = Counter(p["topic"] for p in EVALUATION_DATASET)

    wrong_counts = [len(p["wrong_answers"]) for p in EVALUATION_DATASET]
    all_wrong = [
        wa
        for p in EVALUATION_DATASET
        for wa in p["wrong_answers"]
    ]
    by_error_type = Counter(wa["expected_error_type"] for wa in all_wrong)
    total_wrong = len(all_wrong)

    missing_wrong: list[str] = [
        p["problem_id"]
        for p in EVALUATION_DATASET
        if len(p["wrong_answers"]) < 2
    ]

    print(f"Total problems: {total_problems}")
    print()
    print("By difficulty:")
    for level in DIFFICULTIES:
        count = by_difficulty.get(level, 0)
        print(f"  {level + ':':<8} {count:>3}  ({_pct(count, total_problems)}%)")
    print()
    print("By topic:")
    for topic in TOPICS:
        count = by_topic.get(topic, 0)
        print(f"  {topic + ':':<18} {count:>3}  ({_pct(count, total_problems)}%)")
    print()
    print("Wrong answers per problem:")
    print(f"  min: {min(wrong_counts)}")
    print(f"  max: {max(wrong_counts)}")
    print(f"  avg: {sum(wrong_counts) / len(wrong_counts):.1f}")
    print()
    print("Wrong answers by error type:")
    for error_type in ERROR_TYPES:
        count = by_error_type.get(error_type, 0)
        print(f"  {error_type + ':':<20} {count:>3}  ({_pct(count, total_wrong)}%)")
    print()
    if missing_wrong:
        print(f"Problems missing a wrong answer: {', '.join(missing_wrong)}")
    else:
        print("Problems missing a wrong answer: None")

    failed = False
    if total_problems < 50:
        failed = True
    if missing_wrong:
        failed = True
    if any(by_difficulty.get(level, 0) == 0 for level in DIFFICULTIES):
        failed = True
    if total_wrong > 0:
        for error_type in ERROR_TYPES:
            if by_error_type.get(error_type, 0) / total_wrong > 0.60:
                failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
