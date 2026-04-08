"""Engine unit tests with mock LLM."""

from __future__ import annotations

import pytest

from nlgeo.engine import Engine
from nlgeo.types import Dialect, IntentResult


def test_engine_mock_pipeline(utility_context, mock_llm):
    mock_llm.set_response(
        "pipes near river",
        IntentResult(
            predicate="ST_DWithin",
            subject_table="water_mains",
            ref_table="gas_lines",
            distance=100.0,
            distance_unit="meters",
            assumptions={"near": "within 100 meters (utility_network default)"},
        ),
    )
    eng = Engine(llm="mock", context=utility_context, mock=mock_llm)
    res = eng.translate("pipes near river")
    assert "ST_DWithin" in res.query
    assert res.dialect == Dialect.POSTGIS
    assert res.confidence >= 0.6


def test_dialect_routing_geopandas(utility_context, mock_llm):
    mock_llm.set_response(
        "parcels near zone",
        IntentResult(
            predicate="ST_DWithin",
            subject_table="parcels",
            ref_table="flood_zones",
            distance=100.0,
            distance_unit="meters",
        ),
    )
    eng = Engine(llm="mock", context=utility_context, mock=mock_llm)
    res = eng.translate("parcels near zone", dialect=Dialect.GEOPANDAS)
    assert res.dialect == Dialect.GEOPANDAS
    assert ".buffer(" in res.query


def test_dialect_routing_postgis_vs_geopandas(utility_context, mock_llm):
    mock_llm.set_response(
        "same nl",
        IntentResult(
            predicate="ST_DWithin",
            subject_table="manholes",
            ref_table="gas_lines",
            distance=20.0,
            distance_unit="meters",
            assumptions={},
        ),
    )
    eng = Engine(llm="mock", context=utility_context, mock=mock_llm)
    pg = eng.translate("same nl", dialect=Dialect.POSTGIS)
    gp = eng.translate("same nl", dialect=Dialect.GEOPANDAS)
    assert "INNER JOIN" in pg.query or "ST_DWithin" in pg.query
    assert "import geopandas" in gp.query
    assert pg.dialect != gp.dialect


def test_alternatives_populated(utility_context, mock_llm):
    mock_llm.set_response(
        "near query",
        IntentResult(
            predicate="ST_DWithin",
            subject_table="manholes",
            ref_table="gas_lines",
            distance=50.0,
            distance_unit="feet",
            assumptions={},
        ),
    )
    eng = Engine(llm="mock", context=utility_context, mock=mock_llm)
    result = eng.translate("near query", with_alternatives=True)
    assert len(result.alternatives) == 2
    assert result.alternatives[0].bind_params != result.alternatives[1].bind_params
