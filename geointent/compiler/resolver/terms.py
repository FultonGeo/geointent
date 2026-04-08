"""Resolve ambiguous spatial terms using SpatialContext and domain tables."""

from __future__ import annotations

from geointent.compiler.resolver import domains
from geointent.types import ResolvedSpatialTerm, SpatialContext
from geointent.units import to_meters


def _domain_or_default(ctx: SpatialContext) -> str:
    d = ctx.domain
    if d in ("utility_network", "parcel", "environmental"):
        return d
    return "utility_network"


def resolve_near(ctx: SpatialContext) -> ResolvedSpatialTerm:
    domain = _domain_or_default(ctx)
    m = domains.default_distance_meters(domain, "near")
    assert m is not None
    suffix = domains.assumption_suffix(domain)
    return ResolvedSpatialTerm(
        predicate="ST_DWithin",
        distance_meters=m,
        assumption=f"near interpreted as within {m:.0f} meters{suffix}",
    )


def resolve_adjacent(ctx: SpatialContext) -> ResolvedSpatialTerm:
    domain = _domain_or_default(ctx)
    m = domains.default_distance_meters(domain, "adjacent")
    assert m is not None
    suffix = domains.assumption_suffix(domain)
    return ResolvedSpatialTerm(
        predicate="ST_DWithin",
        distance_meters=m,
        assumption=f"adjacent interpreted as within {m:.0f} meters{suffix}",
    )


def resolve_along(ctx: SpatialContext) -> ResolvedSpatialTerm:
    domain = _domain_or_default(ctx)
    m = domains.default_distance_meters(domain, "along")
    assert m is not None
    suffix = domains.assumption_suffix(domain)
    return ResolvedSpatialTerm(
        predicate="ST_DWithin",
        distance_meters=m,
        assumption=f"along interpreted as corridor within {m:.0f} meters{suffix}",
    )


def resolve_within_term(ctx: SpatialContext) -> ResolvedSpatialTerm:
    """Spatial 'within' as distance buffer (not ST_Within topology)."""
    domain = _domain_or_default(ctx)
    m = domains.default_distance_meters(domain, "within")
    assert m is not None
    suffix = domains.assumption_suffix(domain)
    return ResolvedSpatialTerm(
        predicate="ST_DWithin",
        distance_meters=m,
        assumption=f"within interpreted as within {m:.0f} meters{suffix}",
    )


def resolve_beside(ctx: SpatialContext) -> ResolvedSpatialTerm:
    domain = _domain_or_default(ctx)
    m = domains.default_distance_meters(domain, "beside")
    assert m is not None
    suffix = domains.assumption_suffix(domain)
    return ResolvedSpatialTerm(
        predicate="ST_DWithin",
        distance_meters=m,
        assumption=f"beside interpreted as within {m:.0f} meters{suffix}",
    )


def resolve_surrounding(ctx: SpatialContext) -> ResolvedSpatialTerm:
    domain = _domain_or_default(ctx)
    m = domains.default_distance_meters(domain, "surrounding")
    assert m is not None
    suffix = domains.assumption_suffix(domain)
    return ResolvedSpatialTerm(
        predicate="ST_DWithin",
        distance_meters=m,
        assumption=f"surrounding interpreted as within {m:.0f} meters{suffix}",
    )


def resolve_inside(ctx: SpatialContext) -> ResolvedSpatialTerm:
    domain = _domain_or_default(ctx)
    suffix = domains.assumption_suffix(domain)
    return ResolvedSpatialTerm(
        predicate="ST_Within",
        distance_meters=None,
        assumption=f"inside interpreted as ST_Within (topological containment){suffix}",
    )


def resolve_outside(ctx: SpatialContext) -> ResolvedSpatialTerm:
    domain = _domain_or_default(ctx)
    suffix = domains.assumption_suffix(domain)
    return ResolvedSpatialTerm(
        predicate="ST_Disjoint",
        distance_meters=None,
        assumption=f"outside interpreted as no intersection / outside polygon{suffix}",
    )


def distance_from_intent_to_meters(distance: float | None, unit: str | None) -> float | None:
    if distance is None:
        return None
    u = (unit or "meters").lower()
    return to_meters(float(distance), u)
