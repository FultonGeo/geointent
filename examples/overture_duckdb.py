#!/usr/bin/env python3
"""Show DuckDB spatial SQL for an Overture-style schema (no live DB required)."""

from __future__ import annotations

import nlgeo
from nlgeo.llm.backends.mock import MockLLMBackend
from nlgeo.types import Dialect, IntentResult, SpatialContext


def main() -> None:
    schema = nlgeo.Schema.from_dict(
        {
            "tables": [
                {
                    "name": "places",
                    "geom_column": "geometry",
                    "geom_type": "GEOMETRY",
                    "srid": 4326,
                    "columns": ["id", "names", "geometry"],
                }
            ]
        }
    )
    ctx = SpatialContext(
        schema=schema,
        domain="environmental",
        units="meters",
        srid=4326,
        bbox=(-86.35, 39.63, -85.95, 39.95),
    )
    mock = MockLLMBackend()
    mock.set_response(
        "places near a park",
        IntentResult(
            predicate="ST_DWithin",
            subject_table="places",
            ref_table="places",
            distance=500.0,
            distance_unit="meters",
            filters={},
            assumptions={},
        ),
    )
    engine = nlgeo.Engine(llm="mock", context=ctx, mock=mock)
    result = engine.translate("places near a park", dialect=Dialect.DUCKDB)
    print(result.query)


if __name__ == "__main__":
    main()
