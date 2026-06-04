"""Print Phase 3 evaluation metrics (detection rate, misclassifications, parse failures)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.benchmark_runner import run_evaluation_benchmark

if __name__ == "__main__":
    report = run_evaluation_benchmark()
    for line in report.summary_lines():
        print(line)
    raise SystemExit(0 if report.failed == 0 else 1)
