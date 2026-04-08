"""Ambiguity resolver unit tests."""

from __future__ import annotations

import pytest

from nlgeo.compiler.resolver import terms
from nlgeo.types import SpatialContext


def test_resolver_near_utility(utility_context):
    r = terms.resolve_near(utility_context)
    assert r.predicate == "ST_DWithin"
    assert r.distance_meters == pytest.approx(50.0)
    assert "utility_network" in r.assumption.lower()


def test_resolver_near_parcel(parcel_schema):
    ctx = SpatialContext(
        schema=parcel_schema,
        domain="parcel",
        units="feet",
        srid=4326,
    )
    r = terms.resolve_near(ctx)
    assert r.distance_meters == pytest.approx(25.0)


def test_resolver_near_env(parcel_schema):
    ctx = SpatialContext(
        schema=parcel_schema,
        domain="environmental",
        units="meters",
        srid=4326,
    )
    r = terms.resolve_near(ctx)
    assert r.distance_meters == pytest.approx(200.0)


def test_resolver_inside(utility_context):
    r = terms.resolve_inside(utility_context)
    assert r.predicate == "ST_Within"
    assert r.distance_meters is None
