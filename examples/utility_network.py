#!/usr/bin/env python3
"""PostGIS-style output for a utility network query (mock LLM — no database required)."""

from __future__ import annotations

import nlgeo
from nlgeo.llm.backends.mock import MockLLMBackend
from nlgeo.types import IntentResult, SpatialContext


def main() -> None:
    schema = nlgeo.Schema.from_dict(
        {
            "tables": [
                {
                    "name": "gas_lines",
                    "geom_column": "geom",
                    "geom_type": "LINESTRING",
                    "srid": 2965,
                    "columns": ["id", "name", "geom"],
                },
                {
                    "name": "manholes",
                    "geom_column": "geom",
                    "geom_type": "POINT",
                    "srid": 2965,
                    "columns": ["id", "last_inspection", "geom"],
                },
            ]
        }
    )
    ctx = SpatialContext(
        schema=schema,
        domain="utility_network",
        units="feet",
        srid=2965,
        bbox=(-86.20, 39.70, -86.10, 39.80),
    )
    mock = MockLLMBackend()
    mock.set_response(
        "manholes within 50 feet of a gas line",
        IntentResult(
            predicate="ST_DWithin",
            subject_table="manholes",
            ref_table="gas_lines",
            distance=50.0,
            distance_unit="feet",
            filters={},
            assumptions={},
        ),
    )
    engine = nlgeo.Engine(llm="mock", context=ctx, mock=mock)
    result = engine.translate("manholes within 50 feet of a gas line")
    print(result.query)
    print("confidence:", round(result.confidence, 3))


if __name__ == "__main__":
    main()
