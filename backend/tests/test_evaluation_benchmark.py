"""Phase 3 — dataset-driven benchmark with aggregate metrics assertions."""
import pytest

from tests.benchmark_runner import run_evaluation_benchmark


def test_evaluation_benchmark_full_pass(validator):
    """
    All Phase 2 labeled wrong steps must be non-equivalent and correctly classified.
    Failing cases are listed in the assertion message via BenchmarkReport.summary_lines().
    """
    report = run_evaluation_benchmark(validator)
    if report.failed:
        detail = "\n".join(report.summary_lines())
        pytest.fail(
            f"Benchmark {report.passed}/{report.total} passed "
            f"(detection rate {report.detection_rate:.1%}).\n{detail}"
        )
