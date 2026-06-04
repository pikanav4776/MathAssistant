"""
Phase 1 step 2 — normalization + equivalence golden cases.

All exponents use ^ (not **), matching the parser's user-facing notation.
"""

EQUIVALENCE_CASES: list[dict[str, str]] = [
    {
        "problem": "(x+3)*(x+2)",
        "expected": "x^2+5*x+6",
        "student": "x^2+6*x+5",
    },
    {
        "problem": "(x*y+76-x*7)*68",
        "expected": "68*x*y-476*x+5168",
        "student": "68*x+6708-7*y",
    },
    {
        "problem": "(9*x-7*y)*(8*z-7*y)",
        "expected": "72*x*z-63*x*y-56*y*z+49*y^2",
        "student": "72*x^2-63*x*y-56*y*z+49*y^2",
    },
    {
        "problem": "4*a-2*a+6*a-7*z",
        "expected": "8*a-7*z",
        "student": "-4*a-7*z",
    },
    {
        "problem": "2+3*x*y*z-2*x*y*z-6",
        "expected": "x*y*z-4",
        "student": "5*x*y*z-2*y*z+6",
    },
    {
        "problem": "67*b-420*m+2*m",
        "expected": "67*b-418*m",
        "student": "86*b-418*m",
    },
    {
        "problem": "89*x*k-34*x*k+3",
        "expected": "55*x*k+3",
        "student": "89*x*k-34*x*k-3",
    },
    {
        "problem": "(71*f-36*c)*(f-14*c)",
        "expected": "71*f^2-1030*f*c+504*c^2",
        "student": "71*f-994*f+504*c^2",
    },
    {
        "problem": "c^2*(a^2+b^2+c^2)",
        "expected": "a^2*c^2+b^2*c^2+c^4",
        "student": "c^2*a^2+b^2*c^2-c^3",
    },
    {
        "problem": "(a-b+2*c)*(a-b+2*c)",
        "expected": "a^2-2*a*b+4*a*c-4*b*c+b^2+4*c^2",
        "student": "a^2-b^2+4*c^3",
    },
]
