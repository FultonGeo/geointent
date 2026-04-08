"""
Per-domain default distances (meters) for ambiguous spatial terms.
Domains: utility_network, parcel, environmental.
"""

from __future__ import annotations

from typing import Literal

DomainName = Literal["utility_network", "parcel", "environmental"]

# Distances in meters per term; None means predicate-only (no buffer distance).
_THRESHOLDS: dict[str, dict[str, float | None]] = {
    "utility_network": {
        "near": 50.0,
        "adjacent": 5.0,
        "along": 15.0,
        "within": 100.0,
        "beside": 10.0,
        "surrounding": 75.0,
        "inside": None,
        "outside": None,
    },
    "parcel": {
        "near": 25.0,
        "adjacent": 3.0,
        "along": 10.0,
        "within": 50.0,
        "beside": 8.0,
        "surrounding": 40.0,
        "inside": None,
        "outside": None,
    },
    "environmental": {
        "near": 200.0,
        "adjacent": 30.0,
        "along": 50.0,
        "within": 500.0,
        "beside": 40.0,
        "surrounding": 300.0,
        "inside": None,
        "outside": None,
    },
}


def default_distance_meters(domain: str, term: str) -> float | None:
    d = _THRESHOLDS.get(domain, _THRESHOLDS["utility_network"])
    return d.get(term)


def assumption_suffix(domain: str) -> str:
    return f" ({domain} domain default)"


def threshold_tables() -> dict[str, dict[str, float | None]]:
    """Copy of per-domain default distances (meters) for prompts and tests."""
    return {k: dict(v) for k, v in _THRESHOLDS.items()}
