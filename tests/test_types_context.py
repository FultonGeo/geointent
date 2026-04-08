"""SpatialContext validation."""

from __future__ import annotations

import pytest

from nlgeo.types import SpatialContext


def test_spatial_context_srid_accepts_known(utility_schema):
    for srid in (4326, 2965, 3857):
        ctx = SpatialContext(schema=utility_schema, srid=srid)
        assert ctx.srid == srid


def test_spatial_context_srid_rejects_unknown(utility_schema):
    with pytest.raises(ValueError, match="Unknown SRID"):
        SpatialContext(schema=utility_schema, srid=9999)
