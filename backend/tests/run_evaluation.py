"""Run Phase 2 evaluation benchmark against the classifier."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import StepValidator, ParseError
from tests.evaluation_dataset import EVALUATION_DATASET

v = StepValidator()

print("=" * 78)
print("PHASE 2 — Evaluation dataset (classification labels)")
print("=" * 78)

passed = 0
failed = 0
total = 0
by_type: dict[str, int] = {}

for item in EVALUATION_DATASET:
    item_id = item["id"]
    correct = item["correct"]
    for wrong in item["wrongs"]:
        total += 1
        expr = wrong["expression"]
        label = wrong["error_type"]
        by_type[label] = by_type.get(label, 0) + 1
        tag = f"{item_id} ({label})"

        try:
            result = v.validate(expr, correct)
            equiv = result["is_equivalent"]
            got = (
                result["error_classification"]["error_type"]
                if result["error_classification"]
                else "correct"
            )

            equiv_ok = not equiv
            class_ok = got == label
            ok = equiv_ok and class_ok

            if ok:
                passed += 1
                print(f"PASS  {tag}")
            else:
                failed += 1
                print(f"FAIL  {tag}")
                if equiv:
                    print("       student incorrectly marked equivalent")
                if not class_ok:
                    print(f"       expected {label}, got {got}")
                    if result["error_classification"]:
                        reason = result["error_classification"].get("reason", "")
                        if reason:
                            print(f"       reason: {reason[:72]}")
        except ParseError as exc:
            failed += 1
            print(f"FAIL  {tag}")
            print(f"       parse error: {exc}")

print()
print("=" * 78)
print(f"Score: {passed}/{total} passed")
print(f"Labels in dataset: {dict(sorted(by_type.items()))}")
if failed:
    print(f"Failures: {failed}")
else:
    print("All evaluation cases passed.")
