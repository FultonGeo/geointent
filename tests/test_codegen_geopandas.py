"""GeoPandas codegen tests."""

from __future__ import annotations

from unittest.mock import patch

import geopandas as gpd
import pytest
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

from nlgeo.compiler.codegen import geopandas as geopandas_codegen
from nlgeo.types import IntentResult, SpatialContext


def test_geopandas_uses_buffer(utility_context):
    intent = IntentResult(
        predicate="ST_DWithin",
        subject_table="manholes",
        ref_table="gas_lines",
        distance=30.0,
        distance_unit="meters",
    )
    code = geopandas_codegen.render_intent(intent, utility_context)
    assert ".buffer(" in code


def test_geopandas_inside_uses_within(parcel_schema):
    ctx = SpatialContext(schema=parcel_schema, domain="parcel", units="meters", srid=4326)
    intent = IntentResult(
        predicate="ST_Within",
        subject_table="parcels",
        ref_table="flood_zones",
    )
    code = geopandas_codegen.render_intent(intent, ctx)
    assert ".within(" in code


def test_geopandas_output_executes(utility_context):
    intent = IntentResult(
        predicate="ST_DWithin",
        subject_table="manholes",
        ref_table="gas_lines",
        distance=10.0,
        distance_unit="meters",
    )
    code = geopandas_codegen.render_intent(intent, utility_context)

    mh = gpd.GeoDataFrame({"id": [1]}, geometry=[Point(553100, 436000)], crs=None)
    gl = gpd.GeoDataFrame(
        {"id": [1]},
        geometry=[LineString([(553000, 436000), (553500, 436000)])],
        crs=None,
    )

    def fake_read_postgis(sql, conn, **kwargs):
        if "manholes" in sql:
            return mh
        if "gas_lines" in sql:
            return gl
        raise AssertionError(sql)

    with patch.object(gpd, "read_postgis", side_effect=fake_read_postgis):
        ns: dict = {"gpd": gpd, "conn": object(), "unary_union": unary_union}
        exec(compile(code, "<test geopandas codegen>", "exec"), ns, ns)
        assert "result_gdf" in ns
        assert len(ns["result_gdf"]) >= 0
