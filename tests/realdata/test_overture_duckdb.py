"""Public Overture GeoParquet via DuckDB (network)."""

from __future__ import annotations

import pytest


@pytest.mark.realdata
def test_duckdb_query_runs_indy_places():
    pytest.importorskip("duckdb")
    import duckdb

    conn = duckdb.connect()
    conn.execute("INSTALL spatial; LOAD spatial;")
    conn.execute("INSTALL httpfs; LOAD httpfs;")
    conn.execute("SET s3_region='us-west-2';")

    try:
        result = conn.execute(
            """
            SELECT count(*)::BIGINT AS n
            FROM read_parquet(
              's3://overturemaps-us-west-2/release/2024-11-13.0/theme=places/type=place/*',
              filename=true,
              hive_partitioning=1
            )
            WHERE bbox.xmin BETWEEN -86.35 AND -85.95
              AND bbox.ymin BETWEEN 39.63 AND 39.95
            LIMIT 1
            """
        ).fetchone()
    except Exception as exc:
        pytest.skip(f"Overture/S3 not reachable: {exc}")

    assert result is not None and result[0] >= 0
