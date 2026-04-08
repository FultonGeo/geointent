"""Ambiguity resolvers for spatial terms."""

from nlgeo.compiler.resolver.terms import (
    resolve_adjacent,
    resolve_along,
    resolve_beside,
    resolve_inside,
    resolve_near,
    resolve_outside,
    resolve_surrounding,
    resolve_within_term,
)

__all__ = [
    "resolve_near",
    "resolve_adjacent",
    "resolve_along",
    "resolve_within_term",
    "resolve_beside",
    "resolve_surrounding",
    "resolve_inside",
    "resolve_outside",
]
