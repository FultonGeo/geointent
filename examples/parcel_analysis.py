#!/usr/bin/env python3
"""Parcel / flood-zone style query with GeoJSON filter output (mock LLM)."""

from __future__ import annotations

import json

import nlgeo
from nlgeo.llm.backends.mock import MockLLMBackend
from nlgeo.types import Dialect, IntentResult, SpatialContext


def main() -> None:
    schema = nlgeo.Schema.from_dict(
        {
            "tables": [
                {
                    "name": "parcels",
                    "geom_column": "geom",
                    "geom_type": "POLYGON",
                    "srid": 4326,
                    "columns": ["id", "parcel_id", "geom"],
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
    ctx = SpatialContext(schema=schema, domain="parcel", units="feet", srid=4326)
    mock = MockLLMBackend()
    mock.set_response(
        "parcels inside flood zone AE",
        IntentResult(
            predicate="ST_Within",
            subject_table="parcels",
            ref_table="flood_zones",
            distance=None,
            distance_unit=None,
            filters={"zone_code": "AE"},
            assumptions={},
        ),
    )
    engine = nlgeo.Engine(llm="mock", context=ctx, mock=mock)
    result = engine.translate("parcels inside flood zone AE", dialect=Dialect.GEOJSON)
    print(json.dumps(json.loads(result.query), indent=2))


if __name__ == "__main__":
    main()
