"""Portfolio-grade classifier evaluation against the labeled dataset."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from evaluation_dataset import FLAT_DATASET  # noqa: E402
from main import StepValidator  # noqa: E402

LABELS = ["distribution_error", "sign_error", "arithmetic_error", "unknown"]


def _pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator * 100 / denominator


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def main() -> None:
    validator = StepValidator()
    total_entries = len(FLAT_DATASET)

    print("MathAssistant Classifier Evaluation")
    print()

    parsed_rows: list[dict] = []
    parse_failures: list[tuple[str, str, str]] = []

    for index, row in enumerate(FLAT_DATASET, start=1):
        if index % 10 == 0 or index == total_entries:
            print(f"Evaluating... {index}/{total_entries}")

        problem_id = row["problem_id"]
        wrong_step = row["wrong_step"]
        correct_step = row["correct_step"]
        expected = row["expected_error_type"]

        try:
            validator.parser(wrong_step)
            validator.parser(correct_step)
            result = validator.validate(wrong_step, correct_step)
        except Exception as exc:
            parse_failures.append((problem_id, wrong_step, str(exc)))
            continue

        if result["is_equivalent"]:
            predicted = "unknown"
        elif result["error_classification"] is None:
            predicted = "unknown"
        else:
            predicted = result["error_classification"]["error_type"]

        parsed_rows.append(
            {
                "problem_id": problem_id,
                "wrong_step": wrong_step,
                "expected": expected,
                "predicted": predicted,
            }
        )

    parsed_total = len(parsed_rows)
    parse_success = parsed_total
    print()
    print("Dataset summary:")
    print(f"  Total entries: {total_entries}")
    print(
        f"  Parse success rate: {parse_success}/{total_entries} "
        f"({_pct(parse_success, total_entries):.1f}%)"
    )
    print()

    print("Parse failures:")
    if parse_failures:
        for problem_id, wrong_step, message in parse_failures:
            print(f"  {problem_id}, {wrong_step}: {message}")
    else:
        print("  None")
    print()

    confusion: Counter[tuple[str, str]] = Counter()
    for row in parsed_rows:
        confusion[(row["expected"], row["predicted"])] += 1

    header = "                        Predicted"
    col_header = "                  dist   sign  arith  unknown"
    print("Confusion matrix:")
    print(header)
    print(col_header)
    for actual in ("distribution_error", "sign_error", "arithmetic_error"):
        short = {"distribution_error": "dist", "sign_error": "sign", "arithmetic_error": "arith"}[
            actual
        ]
        cells = [
            confusion.get((actual, predicted), 0)
            for predicted in LABELS
        ]
        print(
            f"   Actual  {short:<5}| {cells[0]:>4} | {cells[1]:>4} | "
            f"{cells[2]:>4} | {cells[3]:>4} |"
        )
    print()

    per_class: dict[str, dict[str, float]] = {}
    print("Per-class metrics:")
    print(f"  {'Error type':<22} Precision  Recall   F1")
    f1_scores: list[float] = []
    for label in ("distribution_error", "sign_error", "arithmetic_error"):
        tp = confusion.get((label, label), 0)
        fp = sum(
            confusion.get((other, label), 0)
            for other in ("distribution_error", "sign_error", "arithmetic_error")
            if other != label
        )
        fn = sum(
            confusion.get((label, other), 0)
            for other in LABELS
            if other != label
        )
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = _f1(precision, recall)
        f1_scores.append(f1)
        per_class[label] = {"precision": precision, "recall": recall, "f1": f1}
        print(f"  {label:<22} {precision:.2f}       {recall:.2f}     {f1:.2f}")
    print()

    macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
    print(f"Macro F1: {macro_f1:.2f}")
    print()

    correct = sum(1 for row in parsed_rows if row["predicted"] == row["expected"])
    print(
        f"Overall accuracy: {correct}/{parsed_total} "
        f"({_pct(correct, parsed_total):.1f}%)"
    )
    print()

    unknown_count = sum(1 for row in parsed_rows if row["predicted"] == "unknown")
    print(
        f"Unknown rate: {unknown_count}/{parsed_total} "
        f"({_pct(unknown_count, parsed_total):.1f}%)"
    )
    if _pct(unknown_count, parsed_total) > 10:
        print("WARNING: unknown rate exceeds 10%. Review classify_error() rules.")
    print()

    misclassified = [
        row for row in parsed_rows if row["predicted"] != row["expected"]
    ]
    print("Misclassified entries:")
    if misclassified:
        for row in misclassified:
            print(
                f"  {row['problem_id']}, {row['wrong_step']}, "
                f"expected={row['expected']}, got={row['predicted']}"
            )
    else:
        print("  None")


if __name__ == "__main__":
    main()
