"""PostGIS schema introspection (integration — requires seeded local PostGIS)."""

from __future__ import annotations

import pytest

import nlgeo


@pytest.mark.integration
def test_schema_from_postgis(postgis_conn):
    s = nlgeo.Schema.from_postgis(postgis_conn)
    names = {t.name for t in s.tables}
    assert "manholes" in names
    mh = next(t for t in s.tables if t.name == "manholes")
    assert mh.geom_column == "geom"
    assert mh.srid == 2965
