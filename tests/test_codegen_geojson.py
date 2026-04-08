"""GeoJSON filter codegen tests."""

from __future__ import annotations

import json

from geointent.compiler.codegen import geojson as geojson_codegen
from geointent.types import IntentResult, SpatialContext


def test_geojson_filter_valid(parcel_schema):
    ctx = SpatialContext(schema=parcel_schema, domain="parcel", units="meters", srid=4326)
    intent = IntentResult(
        predicate="ST_DWithin",
        subject_table="parcels",
        ref_table="flood_zones",
        distance=500.0,
        distance_unit="feet",
    )
    raw = geojson_codegen.render_intent(intent, ctx)
    data = json.loads(raw)
    assert data["op"] == "spatial"
    assert data["subject"] == "parcels"
    assert "distance_m" in data
    assert float(data["distance_m"]) > 0
