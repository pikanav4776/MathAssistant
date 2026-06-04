"""
Phase 2 — labeled evaluation benchmark.

Each item: problem (context), correct step, and one or more wrong steps with
expected error_type labels for the classifier.

Expressions use ^ (not **), matching the parser. Rows ported from
equivalence_cases.py with labels from the Phase 1 classification review.
"""

EVALUATION_DATASET: list[dict] = [
    {
        "id": "expand-binomial-01",
        "problem": "(x+3)*(x+2)",
        "correct": "x^2+5*x+6",
        "wrongs": [ 
            {"expression": "x^2+6*x+5", "error_type": "arithmetic_error"},
        ],
    },
    {
        "id": "distribute-scalar-02",
        "problem": "(x*y+76-x*7)*68",
        "correct": "68*x*y-476*x+5168",
        "wrongs": [
            {"expression": "68*x+6708-7*y", "error_type": "distribution_error"},
        ],
    },
    {
        "id": "expand-trinomial-03",
        "problem": "(9*x-7*y)*(8*z-7*y)",
        "correct": "72*x*z-63*x*y-56*y*z+49*y^2",
        "wrongs": [
            {"expression": "72*x^2-63*x*y-56*y*z+49*y^2", "error_type": "distribution_error"},
        ],
    },
    {
        "id": "combine-like-terms-04",
        "problem": "4*a-2*a+6*a-7*z",
        "correct": "8*a-7*z",
        "wrongs": [
            {"expression": "-4*a-7*z", "error_type": "arithmetic_error"},
        ],
    },
    {
        "id": "combine-multivar-05",
        "problem": "2+3*x*y*z-2*x*y*z-6",
        "correct": "x*y*z-4",
        "wrongs": [
            {"expression": "5*x*y*z-2*y*z+6", "error_type": "distribution_error"},
        ],
    },
    {
        "id": "combine-coeff-06",
        "problem": "67*b-420*m+2*m",
        "correct": "67*b-418*m",
        "wrongs": [
            {"expression": "86*b-418*m", "error_type": "arithmetic_error"},
        ],
    },
    {
        "id": "sign-constant-07",
        "problem": "89*x*k-34*x*k+3",
        "correct": "55*x*k+3",
        "wrongs": [
            {"expression": "89*x*k-34*x*k-3", "error_type": "sign_error"},
        ],
    },
    {
        "id": "expand-product-08",
        "problem": "(71*f-36*c)*(f-14*c)",
        "correct": "71*f^2-1030*f*c+504*c^2",
        "wrongs": [
            {"expression": "71*f-994*f+504*c^2", "error_type": "distribution_error"},
        ],
    },
    {
        "id": "expand-monomial-09",
        "problem": "c^2*(a^2+b^2+c^2)",
        "correct": "a^2*c^2+b^2*c^2+c^4",
        "wrongs": [
            {"expression": "c^2*a^2+b^2*c^2-c^3", "error_type": "distribution_error"},
        ],
    },
    {
        "id": "square-binomial-10",
        "problem": "(a-b+2*c)*(a-b+2*c)",
        "correct": "a^2-2*a*b+4*a*c-4*b*c+b^2+4*c^2",
        "wrongs": [
            {"expression": "a^2-b^2+4*c^3", "error_type": "distribution_error"},
        ],
    },
]
