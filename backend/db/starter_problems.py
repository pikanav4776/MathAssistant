"""Curated starter problems surfaced in the problem-selection UI."""

from __future__ import annotations

# Twelve problems covering all five topics and three difficulty levels.
STARTER_PROBLEM_IDS: tuple[str, ...] = (
    "dist_001",  # easy distribution
    "dist_003",  # medium distribution
    "sign_001",  # easy simplification
    "simp_002",  # easy simplification
    "arith_002",  # medium simplification / arithmetic
    "dexp_001",  # easy FOIL
    "dexp_005",  # medium FOIL
    "lin_001",  # easy linear steps
    "lin_005",  # medium linear steps
    "mhop_001",  # easy multihop
    "mhop_005",  # medium multihop
    "mhop_012",  # hard multihop
)

_STARTER_METADATA: dict[str, dict[str, str]] = {
    "dist_001": {"difficulty": "easy", "topic": "distribution"},
    "dist_003": {"difficulty": "medium", "topic": "distribution"},
    "sign_001": {"difficulty": "easy", "topic": "simplification"},
    "simp_002": {"difficulty": "easy", "topic": "simplification"},
    "arith_002": {"difficulty": "medium", "topic": "simplification"},
    "dexp_001": {"difficulty": "easy", "topic": "double_expansion"},
    "dexp_005": {"difficulty": "medium", "topic": "double_expansion"},
    "lin_001": {"difficulty": "easy", "topic": "linear_steps"},
    "lin_005": {"difficulty": "medium", "topic": "linear_steps"},
    "mhop_001": {"difficulty": "easy", "topic": "multihop"},
    "mhop_005": {"difficulty": "medium", "topic": "multihop"},
    "mhop_012": {"difficulty": "hard", "topic": "multihop"},
}


def filter_starter_problem_ids(
    *,
    difficulty: str | None = None,
    topic: str | None = None,
) -> list[str]:
    ids = list(STARTER_PROBLEM_IDS)
    if difficulty is not None:
        level = difficulty.lower()
        ids = [
            problem_id
            for problem_id in ids
            if _STARTER_METADATA[problem_id]["difficulty"] == level
        ]
    if topic is not None:
        topic_key = topic.lower()
        ids = [
            problem_id
            for problem_id in ids
            if _STARTER_METADATA[problem_id]["topic"] == topic_key
        ]
    return ids
