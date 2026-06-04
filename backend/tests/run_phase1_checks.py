"""Run Phase 1 step 2 + 3 checks (equivalence + classification)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import StepValidator, ParseError
from tests.equivalence_cases import EQUIVALENCE_CASES

v = StepValidator()

# Intuitive labels for the 10 golden rows (for classification review)
EXPECTED_CLASS_HINT = {
    1: "arithmetic_error",      # swapped 5x and 6
    2: "distribution_error",    # did not distribute *68 properly
    3: "distribution_error",    # wrong/missing product terms after expand
    4: "arithmetic_error",      # -4a vs 8a (not pure sign flip)
    5: "distribution_error",    # extra/missing terms after combine
    6: "arithmetic_error",      # wrong b coefficient
    7: "sign_error",            # +3 vs -3 on constant
    8: "distribution_error",    # missing f^2, wrong linear terms
    9: "distribution_error",    # missing/wrong expanded product term
    10: "distribution_error",   # wrong square expansion; many terms missing
}

print("=" * 78)
print("STEP 2 — Normalization + equivalence")
print("=" * 78)

step2_pass = 0
for i, row in enumerate(EQUIVALENCE_CASES, 1):
    prob, exp, stu = row["problem"], row["expected"], row["student"]
    label = f"Case {i}"
    try:
        prob_ok = v.comparison(prob, exp)["is_equivalent"]
        stu_ok = v.comparison(stu, exp)["is_equivalent"]
        ok = prob_ok and not stu_ok
        note = ""
        if ok:
            step2_pass += 1
        status = "PASS" if ok else "FAIL"
        print(f"{label}: problem==expected={prob_ok}  student==expected={stu_ok}  => {status}{note}")
        if not ok:
            if not prob_ok:
                print(f"         problem normalizes differently from expected")
            if stu_ok:
                print(f"         FALSE POSITIVE: student marked correct")
    except ParseError as e:
        print(f"{label}: PARSE ERROR — {e}  => FAIL")

print(f"\nStep 2 score: {step2_pass}/10")

print("\n" + "=" * 78)
print("STEP 3 — Classification on the 10 cases")
print("=" * 78)

class_counts = {}
for i, row in enumerate(EQUIVALENCE_CASES, 1):
    exp, stu = row["expected"], row["student"]
    try:
        r = v.validate(stu, exp)
        et = r["error_classification"]["error_type"] if r["error_classification"] else "correct"
        class_counts[et] = class_counts.get(et, 0) + 1
        hint = r.get("hint", "")
        expect = EXPECTED_CLASS_HINT.get(i)
        match = "?" if expect is None else ("yes" if et == expect else "no")
        print(f"Case {i}: {et:22}  (expected ~{expect})  match={match}")
        if match == "no" and expect:
            print(f"         reason: {r['error_classification']['reason'][:70]}")
    except Exception as e:
        print(f"Case {i}: ERROR {e}")

print(f"\nClassification distribution: {class_counts}")

print("\n" + "=" * 78)
print("STEP 3 — Targeted sign / arithmetic / distribution probes")
print("=" * 78)

probes = [
    ("sign_error", "2*x+3", "2*x-3"),
    ("arithmetic_error", "2*x+6", "2*x+5"),
    ("distribution_error", "2*x+2*y", "2*x"),  # whole y-term missing
]

for name, expected, student in probes:
    r = v.validate(student, expected)
    got = r["error_classification"]["error_type"] if r["error_classification"] else "correct"
    ok = got == name
    print(f"  {name:22} probe: got {got:22}  => {'PASS' if ok else 'FAIL'}")
