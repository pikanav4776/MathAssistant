"""
Phase 3 — run the Phase 2 evaluation dataset and collect metrics.

Used by pytest (test_evaluation_benchmark) and by run_phase3_report.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from main import ParseError, StepValidator
from tests.evaluation_dataset import FLAT_DATASET


@dataclass
class BenchmarkCaseResult:
    case_id: str
    error_type: str
    expression: str
    passed: bool
    parse_failed: bool = False
    false_positive: bool = False
    expected_label: str = ""
    got_label: str = ""
    reason: str = ""


@dataclass
class BenchmarkReport:
    total: int = 0
    passed: int = 0
    failed: int = 0
    parse_failures: int = 0
    misclassifications: int = 0
    false_positives: int = 0
    by_expected_label: dict[str, int] = field(default_factory=dict)
    failures: list[BenchmarkCaseResult] = field(default_factory=list)

    @property
    def detection_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total

    def summary_lines(self) -> list[str]:
        lines = [
            "=" * 78,
            "PHASE 3 — Evaluation benchmark metrics",
            "=" * 78,
            f"Total wrong-step cases:     {self.total}",
            f"Passed (equiv + label):     {self.passed}",
            f"Failed:                     {self.failed}",
            f"Detection rate:             {self.detection_rate:.1%}",
            f"Parse failures:             {self.parse_failures}",
            f"Misclassifications:         {self.misclassifications}",
            f"False positives (equiv):    {self.false_positives}",
            f"Labels in dataset:          {dict(sorted(self.by_expected_label.items()))}",
        ]
        if self.failures:
            lines.append("")
            lines.append("Failure details:")
            for f in self.failures:
                if f.parse_failed:
                    lines.append(f"  {f.case_id} ({f.error_type}): PARSE ERROR — {f.expression}")
                else:
                    lines.append(
                        f"  {f.case_id} ({f.error_type}): expected {f.expected_label}, "
                        f"got {f.got_label}"
                    )
                    if f.false_positive:
                        lines.append("    student incorrectly marked equivalent")
                    if f.reason:
                        lines.append(f"    reason: {f.reason[:72]}")
        else:
            lines.append("")
            lines.append("All evaluation cases passed.")
        return lines


def run_evaluation_benchmark(validator: StepValidator | None = None) -> BenchmarkReport:
    v = validator or StepValidator()
    report = BenchmarkReport()

    for row in FLAT_DATASET:
        item_id = row["problem_id"]
        correct = row["correct_step"]
        report.total += 1
        expr = row["wrong_step"]
        label = row["expected_error_type"]
        report.by_expected_label[label] = report.by_expected_label.get(label, 0) + 1
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

            case = BenchmarkCaseResult(
                case_id=item_id,
                error_type=label,
                expression=expr,
                passed=ok,
                false_positive=equiv,
                expected_label=label,
                got_label=got,
                reason=(
                    result["error_classification"].get("reason", "")
                    if result["error_classification"]
                    else ""
                ),
            )

            if ok:
                report.passed += 1
            else:
                report.failed += 1
                if equiv:
                    report.false_positives += 1
                if not class_ok:
                    report.misclassifications += 1
                report.failures.append(case)

        except ParseError as exc:
            report.failed += 1
            report.parse_failures += 1
            report.failures.append(
                BenchmarkCaseResult(
                    case_id=item_id,
                    error_type=label,
                    expression=expr,
                    passed=False,
                    parse_failed=True,
                    expected_label=label,
                    got_label=f"parse_error: {exc}",
                )
            )

    return report
