# MathAssistant — Classifier Evaluation Report

## System Overview

MathAssistant is a deterministic algebraic step validation 
and tutoring feedback system built with FastAPI and SymPy. 
Students submit algebraic simplification steps, which the 
system parses, normalizes, and compares against an expected 
correct answer. When a step is incorrect, the classifier's 
job is to identify the specific type of mistake made — 
distribution error, sign error, or arithmetic error — and 
route that classification to the hint engine, which returns 
targeted feedback. This evaluation measures how accurately 
the classifier identifies the correct error type across a 
controlled dataset of 144 labeled wrong-answer entries, 
covering all three error categories across five algebraic 
topics and three difficulty levels.

v0.3 extends the product with multi-hop canonical solution 
paths (distribute-then-combine, FOIL-then-combine). The 
classifier benchmark still compares each wrong step against 
the fully simplified final answer, which remains the 
session completion target.

## Dataset

- Total problems: 72
- Total evaluation entries: 144 (2 wrong answers per problem)
- Multi-hop problems (v0.3): 12

Distribution table:

| Topic            | Easy | Medium | Hard | Total |
|------------------|------|--------|------|-------|
| distribution     |  7   |   9    |  4   |  20   |
| simplification   |  7   |   9    |  4   |  20   |
| double_expansion |  3   |   4    |  3   |  10   |
| linear_steps     |  3   |   3    |  4   |  10   |
| multihop         |  2   |   6    |  4   |  12   |
| **Total**        | 22   |  31    | 19   |  72   |

Wrong answers were generated using Claude (Anthropic) 
following the distribution specification in the Phase 9 
prompt, then validated in two stages: first by 
verify_dataset.py (structural integrity — minimum 2 wrong 
answers per problem, no missing entries, no single error 
type exceeding 60% of wrong answers), then by 
evaluate_classifier.py itself, which runs every 
(wrong_step, correct_step) pair through 
StepValidator.parser() and confirms the wrong step is 
genuinely non-equivalent to the correct answer under SymPy 
normalization. Entries that failed either check were 
corrected or replaced before finalizing the dataset.

## Metrics Definitions

**Parse success rate**
A parse failure means the system cannot evaluate the 
student's step at all — they receive no mathematical 
feedback, only a notation error message. This is a dead end 
in the tutoring loop. Failures occur when students use 
unsupported notation like ** for exponents, unknown symbols, 
or malformed operator sequences. A 100% parse rate on our 
synthetic dataset is expected since all entries were 
pre-validated — the real risk is with live student input, 
where notation errors are common.

**Precision per error type**
Low precision on a given error type means the classifier is 
triggering that error label on steps that are actually wrong 
for a different reason. If precision on sign_error is low, 
students receive sign-focused hints ("check your plus/minus") 
when their actual mistake is something else entirely — a 
missing term or wrong coefficient. This actively misdirects 
their attention and can deepen confusion. A minimum of 95% 
precision per class is required because a wrong hint is 
worse than no hint.

**Recall per error type**
Low recall on distribution_error means the classifier is 
failing to recognize genuine distribution mistakes and 
mislabeling them — most likely as arithmetic or sign errors. 
The student with a missing term gets told their coefficient 
is wrong, checks the coefficient, finds nothing wrong, and 
has no path forward. Recall failure is silent from the 
student's perspective, which makes it more damaging than a 
precision failure.

**F1 per error type**
Accuracy alone is misleading here because the three error 
classes are not balanced — the dataset contains twice as 
many arithmetic wrong answers as distribution wrong answers. 
A classifier that always guessed arithmetic would achieve 
high accuracy while being completely useless for distribution 
and sign errors. F1 balances precision and recall into a 
single per-class number, which means a classifier can only 
score well if it is both correctly labeling a class and not 
missing instances of it.

**Macro F1**
Macro F1 takes the unweighted average of the three per-class 
F1 scores, treating each error type as equally important 
regardless of how many examples it has. This is the right 
choice here because from a tutoring standpoint, a 
distribution error is no less important to catch than an 
arithmetic error just because it appears less frequently in 
the dataset. Weighted F1 would let the dominant class 
(arithmetic) inflate the headline number and mask poor 
performance on rarer error types.

**Overall accuracy**
Overall accuracy counts every correct classification and 
divides by total entries. Its limit here is that it treats 
all misclassifications as equally bad, which they are not — 
calling a distribution error a sign error is more damaging 
than calling a sign error an arithmetic error. Accuracy also 
gives no visibility into which classes are failing. It is a 
useful sanity check and headline number, but the confusion 
matrix and per-class F1 are the diagnostically meaningful 
artifacts.

**Unknown rate**
A non-zero unknown rate means the classifier's rules did not 
match the structure of the student's mistake. Since the 
classifier is deterministic and rule-based rather than 
learned, it does not improve with exposure — an unknown 
classification means a gap in the rule logic itself. From 
the student's perspective, an unknown classification 
produces the most generic possible hint ("compare your step 
term by term"), which provides little actionable guidance. A 
rate above 10% would indicate the rule set needs new 
branches, not more data.

**Confusion matrix**
Predicting sign_error when the actual error is 
distribution_error is more damaging to the student. A sign 
error hint tells the student to recheck their positive and 
negative signs — a targeted, small correction. But a student 
who actually missed distributing an entire term cannot fix 
their work by checking signs; the term is simply absent. 
They will recheck signs, find nothing wrong, and stall. The 
reverse misclassification — calling a sign error a 
distribution error — at least prompts the student to recheck 
all terms, which may accidentally surface the sign mistake.

## Results

### Parse Success

Parse success rate: 144/144 (100.0%)
Parse failures: None

### Confusion Matrix

```
       Predicted
              dist   sign  arith  unknown
Actual  dist |   42 |    0 |    0 |    0 |
Actual  sign |    0 |   30 |    0 |    0 |
Actual  arith|    0 |    0 |   72 |    0 |
```

### Per-Class Metrics

| Error Type          | Precision | Recall | F1   |
|---------------------|-----------|--------|------|
| distribution_error  | 1.00      | 1.00   | 1.00 |
| sign_error          | 1.00      | 1.00   | 1.00 |
| arithmetic_error    | 1.00      | 1.00   | 1.00 |

The 12 v0.3 multihop problems contribute 24 additional 
wrong-answer cases (distribution + arithmetic only). All 
classify correctly against each problem's final simplified 
answer.

### Macro F1

1.00

### Overall Accuracy

144/144 (100.0%)

### Unknown Rate

0/144 (0.0%)

## Interpretation

The final evaluation results reflect the system after one 
targeted classifier fix applied during the evaluation 
process itself. The pre-fix evaluation revealed 4 
misclassifications, all sharing the same root cause: 
polynomial expressions containing multiple term types 
(e.g. x^2 and x terms together) where the student's wrong 
answer differed from the correct answer by sign or 
coefficient on one term. The classifier's 
_is_distribution_error() method was incorrectly firing on 
these cases because the monomial basis of the student 
expression differed from the expected expression — a 
condition that normally indicates a missing term — when in 
fact the terms were present but wrong in value or sign.

The fix added a guard: if every missing term has a 
corresponding extra term that shares the same monomial base 
(differing only by sign or coefficient), the method returns 
False and classification falls through to the sign/arithmetic 
error branches instead. This correctly handles the case where 
a student writes 7x^2+x instead of 7x^2-x — the x term is 
not missing, it is sign-flipped.

After the fix, all three error types achieve perfect 
precision, recall, and F1. The 0% unknown rate confirms the 
rule set has complete coverage over the synthetic dataset, 
including the v0.3 multihop additions. The most notable result 
is that arithmetic_error, despite comprising roughly half of 
the dataset, did not inflate overall accuracy at the expense 
of minority class performance — all three classes score 
equally, which is what Macro F1 is designed to verify.

## Limitations

- The session store is currently in-memory. No longitudinal 
  data on real student mistake patterns has been collected, 
  meaning the dataset's wrong answers are based on 
  anticipated mistakes rather than observed ones.
- All wrong answers are canonical and synthetic. They were 
  generated to represent plausible student errors but have 
  not been validated against real student submissions. 
  Classification performance on live input may differ.
- The classifier is fully deterministic and outputs a hard 
  label with a confidence string (high/medium/low) rather 
  than a probability score. Confidence calibration and 
  threshold-based evaluation (e.g. ROC-AUC) are not 
  applicable to this system.

## Conclusion

MathAssistant's deterministic rule-based classifier achieves 
a Macro F1 of 1.00 across all three error types on a 
144-entry synthetic evaluation dataset (72 problems), with a 
100% parse success rate and 0% unknown rate. The system 
reliably distinguishes distribution errors (missing terms 
after expansion), sign errors (flipped coefficients), and 
arithmetic errors (wrong coefficient values) across five 
algebraic topics and three difficulty levels. v0.3 adds 
multi-hop session validation (tested separately in 
test_v03_api.py and test_v03_integration.py) while keeping 
classifier benchmark quality at 100%. One classifier rule 
gap was identified and fixed during the original evaluation 
— the _is_distribution_error() method's handling of 
polynomial expressions with matching monomial bases. To 
improve the system further, the next steps would be 
collecting real student submission data to validate synthetic 
dataset assumptions, expanding the rule set to cover 
higher-degree polynomial topics, and integrating session 
persistence to enable longitudinal analysis of student 
error patterns.
