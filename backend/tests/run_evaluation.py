"""Run Phase 2/3 evaluation benchmark (human-readable per-case output)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import ParseError, StepValidator
from tests.benchmark_runner import run_evaluation_benchmark
from tests.evaluation_dataset import FLAT_DATASET

v = StepValidator()

print("=" * 78)
print("PHASE 2/3 — Evaluation dataset (classification labels)")
print("=" * 78)

for row in FLAT_DATASET:
    item_id = row["problem_id"]
    correct = row["correct_step"]
    expr = row["wrong_step"]
    label = row["expected_error_type"]
    tag = f"{item_id} ({label})"

    try:
        result = v.validate(expr, correct)
        equiv = result["is_equivalent"]
        got = (
            result["error_classification"]["error_type"]
            if result["error_classification"]
            else "correct"
        )
        ok = (not equiv) and (got == label)
        print(f"{'PASS' if ok else 'FAIL'}  {tag}")
        if not ok:
            if equiv:
                print("       student incorrectly marked equivalent")
            if got != label:
                print(f"       expected {label}, got {got}")
    except ParseError as exc:
        print(f"FAIL  {tag}")
        print(f"       parse error: {exc}")

print()
for line in run_evaluation_benchmark(v).summary_lines():
    print(line)
