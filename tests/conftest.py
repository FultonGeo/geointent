"""Shared pytest fixtures."""

from __future__ import annotations

import os

import pytest

import geointent
from geointent.llm.backends.mock import MockLLMBackend
from geointent.types import IntentResult, SpatialContext


@pytest.fixture
def utility_schema():
    return geointent.Schema.from_dict(
        {
            "tables": [
                {
                    "name": "gas_lines",
                    "geom_column": "geom",
                    "geom_type": "LINESTRING",
                    "srid": 2965,
                    "columns": ["id", "name", "material", "install_year", "geom"],
                },
                {
                    "name": "water_mains",
                    "geom_column": "geom",
                    "geom_type": "LINESTRING",
                    "srid": 2965,
                    "columns": [
                        "id",
                        "diameter_in",
                        "pressure_zone",
                        "last_inspection",
                        "geom",
                    ],
                },
                {
                    "name": "manholes",
                    "geom_column": "geom",
                    "geom_type": "POINT",
                    "srid": 2965,
                    "columns": ["id", "asset_id", "condition_score", "last_inspection", "geom"],
                },
            ]
        }
    )


@pytest.fixture
def parcel_schema():
    return geointent.Schema.from_dict(
        {
            "tables": [
                {
                    "name": "parcels",
                    "geom_column": "geom",
                    "geom_type": "POLYGON",
                    "srid": 4326,
                    "columns": ["id", "parcel_id", "owner", "zoning", "area_sqft", "geom"],
                },
                {
                    "name": "flood_zones",
                    "geom_column": "geom",
                    "geom_type": "MULTIPOLYGON",
                    "srid": 4326,
                    "columns": ["id", "zone_code", "geom"],
                },
            ]
        }
    )


@pytest.fixture
def utility_context(utility_schema):
    return SpatialContext(
        schema=utility_schema,
        domain="utility_network",
        units="feet",
        srid=2965,
        bbox=(-86.20, 39.70, -86.10, 39.80),
    )


@pytest.fixture
def mock_manhole_near_gas(mock_llm):
    """Canned NL → Intent for utility integration-style tests."""
    mock_llm.set_response(
        "manholes within 50 feet of a gas line",
        IntentResult(
            predicate="ST_DWithin",
            subject_table="manholes",
            ref_table="gas_lines",
            distance=50.0,
            distance_unit="feet",
            assumptions={},
        ),
    )


@pytest.fixture
def mock_llm():
    return MockLLMBackend()


@pytest.fixture(scope="session")
def postgis_url():
    return os.environ.get("GEOINTENT_TEST_DB") or os.environ.get(
        "NLGEO_TEST_DB", "postgresql://postgres:nlgeo@localhost:5432/nlgeo_test"
    )


@pytest.fixture(scope="session")
def postgis_engine(postgis_url):
    pytest.importorskip("sqlalchemy")
    from sqlalchemy import create_engine, text

    try:
        eng = create_engine(postgis_url)
        with eng.connect() as c:
            c.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"PostGIS not reachable: {exc}")
    return eng


@pytest.fixture
def postgis_conn(postgis_engine):
    return postgis_engine
