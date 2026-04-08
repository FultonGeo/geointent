"""PostGIS codegen tests."""

from __future__ import annotations

import pytest

from nlgeo.compiler.codegen import postgis
from nlgeo.types import IntentResult, SpatialContext


def test_postgis_dwithin_basic(utility_context):
    intent = IntentResult(
        predicate="ST_DWithin",
        subject_table="manholes",
        ref_table="gas_lines",
        distance=50.0,
        distance_unit="feet",
    )
    sql, params = postgis.render_intent(intent, utility_context)
    assert "ST_DWithin" in sql
    assert len(params) == 1
    assert params[0] == pytest.approx(15.24, rel=1e-3)


def test_postgis_contains(parcel_schema):
    ctx = SpatialContext(
        schema=parcel_schema,
        domain="parcel",
        units="feet",
        srid=4326,
    )
    intent = IntentResult(
        predicate="ST_Within",
        subject_table="parcels",
        ref_table="flood_zones",
    )
    sql, params = postgis.render_intent(intent, ctx)
    assert "ST_Within" in sql
    assert params == []


def test_postgis_date_filter(utility_context):
    intent = IntentResult(
        predicate="ST_DWithin",
        subject_table="manholes",
        ref_table="gas_lines",
        distance=10.0,
        distance_unit="meters",
        filters={"last_inspection_before": "2020-01-01"},
    )
    sql, params = postgis.render_intent(intent, utility_context)
    assert "last_inspection" in sql
    assert "%s" in sql
    assert "2020-01-01" not in sql
    assert params[0] == pytest.approx(10.0)
    assert params[1] == "2020-01-01"


def test_postgis_parameterized(utility_context):
    intent = IntentResult(
        predicate="ST_DWithin",
        subject_table="manholes",
        ref_table="gas_lines",
        distance=25.0,
        distance_unit="feet",
    )
    sql, _params = postgis.render_intent(intent, utility_context)
    assert sql.count("%s") >= 1
    assert "25" not in sql.split("WHERE")[0]


def test_postgis_snapshot_dwithin(snapshot, utility_context):
    intent = IntentResult(
        predicate="ST_DWithin",
        subject_table="manholes",
        ref_table="gas_lines",
        distance=50.0,
        distance_unit="feet",
    )
    sql, _ = postgis.render_intent(intent, utility_context)
    snapshot.assert_match(sql, "postgis_dwithin_feet_50_manholes_gas.sql")


def test_postgis_snapshot_within(snapshot, parcel_schema):
    ctx = SpatialContext(schema=parcel_schema, domain="parcel", units="meters", srid=4326)
    intent = IntentResult(
        predicate="ST_Within",
        subject_table="parcels",
        ref_table="flood_zones",
    )
    sql, _ = postgis.render_intent(intent, ctx)
    snapshot.assert_match(sql, "postgis_within_parcels_flood_zones.sql")


def test_postgis_snapshot_filter(snapshot, utility_context):
    intent = IntentResult(
        predicate="ST_DWithin",
        subject_table="manholes",
        ref_table="gas_lines",
        distance=10.0,
        distance_unit="meters",
        filters={"last_inspection_before": "2019-06-01"},
    )
    sql, _ = postgis.render_intent(intent, utility_context)
    snapshot.assert_match(sql, "postgis_dwithin_with_date_filter.sql")


@pytest.mark.integration
def test_execute_postgis(postgis_conn, utility_context, mock_llm):
    """Same as gate ``test_execute_postgis`` / ``test_generated_sql_executes``."""
    _run_generated_sql_executes(postgis_conn, utility_context, mock_llm)


def _run_generated_sql_executes(postgis_conn, utility_context, mock_llm):
    from nlgeo.engine import Engine

    mock_llm.set_response(
        "manholes within 50 feet of a gas line",
        IntentResult(
            predicate="ST_DWithin",
            subject_table="manholes",
            ref_table="gas_lines",
            distance=50.0,
            distance_unit="feet",
        ),
    )
    eng = Engine(llm="mock", context=utility_context, mock=mock_llm)
    res = eng.translate("manholes within 50 feet of a gas line")
    assert "ST_DWithin" in res.query
    gdf = eng.execute(res, postgis_conn)
    assert len(gdf) >= 1


@pytest.mark.integration
def test_generated_sql_executes(postgis_conn, utility_context, mock_llm):
    _run_generated_sql_executes(postgis_conn, utility_context, mock_llm)
