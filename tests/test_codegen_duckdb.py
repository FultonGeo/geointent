"""DuckDB dialect codegen unit tests."""

from __future__ import annotations

from nlgeo.compiler.codegen import duckdb as duckdb_codegen
from nlgeo.types import IntentResult, SpatialContext


def test_duckdb_dwithin_sql(utility_context):
    intent = IntentResult(
        predicate="ST_DWithin",
        subject_table="places",
        ref_table="places",
        distance=200.0,
        distance_unit="meters",
    )
    sql = duckdb_codegen.render_intent(intent, utility_context)
    assert "ST_DWithin" in sql
    assert "places" in sql


def test_duckdb_bbox_pruning(utility_context):
    intent = IntentResult(
        predicate="ST_DWithin",
        subject_table="buildings",
        ref_table="transportation",
        distance=50.0,
        distance_unit="meters",
    )
    sql = duckdb_codegen.render_intent(intent, utility_context)
    assert "bbox.xmin" in sql
