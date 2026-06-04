"""Run Phase 2/3 evaluation benchmark (human-readable per-case output)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import ParseError, StepValidator
from tests.benchmark_runner import run_evaluation_benchmark
from tests.evaluation_dataset import EVALUATION_DATASET

v = StepValidator()

print("=" * 78)
print("PHASE 2/3 — Evaluation dataset (classification labels)")
print("=" * 78)

for item in EVALUATION_DATASET:
    item_id = item["id"]
    correct = item["correct"]
    for wrong in item["wrongs"]:
        expr = wrong["expression"]
        label = wrong["error_type"]
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
