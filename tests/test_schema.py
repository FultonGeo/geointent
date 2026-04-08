"""Schema serialization and PostGIS introspection."""

from __future__ import annotations

import json

import geointent


def test_schema_from_dict(utility_schema):
    s = utility_schema
    prompt = s.to_prompt_str()
    data = json.loads(prompt)
    assert "tables" in data
    names = {t["name"] for t in data["tables"]}
    assert "gas_lines" in names
    assert "manholes" in names
    for t in data["tables"]:
        assert "geom_column" in t
        assert "srid" in t
