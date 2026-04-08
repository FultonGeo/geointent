"""Schema construction, serialization, and PostGIS introspection."""

from __future__ import annotations

import json
from typing import Any

from nlgeo.types import Schema, TableMeta


def schema_from_dict(data: dict[str, Any]) -> Schema:
    return Schema.model_validate(data)


def schema_to_prompt_str(schema: Schema) -> str:
    """Compact JSON for LLM prompt injection."""
    tables: list[dict[str, Any]] = []
    for t in schema.tables:
        tables.append(
            {
                "name": t.name,
                "geom_column": t.geom_column,
                "geom_type": t.geom_type,
                "srid": t.srid,
                "columns": t.columns,
                **({"description": t.description} if t.description else {}),
            }
        )
    return json.dumps({"tables": tables}, separators=(",", ":"))


def from_postgis(conn: Any) -> Schema:
    """
    Introspect PostGIS: geometry_columns, information_schema.columns, spatial_ref_sys.
    `conn` may be a SQLAlchemy Engine, Connection, or a DBAPI connection with .cursor().
    """
    if hasattr(conn, "connect") and callable(conn.connect):
        engine = conn
        with engine.connect() as c:
            return _from_postgis_connection(c)
    if hasattr(conn, "execute"):
        return _from_postgis_connection(conn)
    return _from_postgis_dbapi(conn)


def _from_postgis_connection(conn: Any) -> Schema:
    from sqlalchemy import text

    rows = conn.execute(
        text(
            """
            SELECT f_table_schema, f_table_name, f_geometry_column, coord_dimension,
                   srid, type
            FROM geometry_columns
            ORDER BY f_table_schema, f_table_name
            """
        )
    ).fetchall()

    tables: list[TableMeta] = []
    for row in rows:
        schema_name, table_name, geom_col, _dim, srid, gtype = row
        full_name = f"{schema_name}.{table_name}" if schema_name != "public" else table_name
        col_rows = conn.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = :tname
                ORDER BY ordinal_position
                """
            ),
            {"schema": schema_name, "tname": table_name},
        ).fetchall()
        columns = [r[0] for r in col_rows]
        tables.append(
            TableMeta(
                name=full_name,
                geom_column=geom_col,
                geom_type=gtype or "GEOMETRY",
                srid=int(srid) if srid is not None else 0,
                columns=columns,
            )
        )
    return Schema(tables=tables)


def _from_postgis_dbapi(conn: Any) -> Schema:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT f_table_schema, f_table_name, f_geometry_column, coord_dimension,
               srid, type
        FROM geometry_columns
        ORDER BY f_table_schema, f_table_name
        """
    )
    rows = cur.fetchall()
    tables: list[TableMeta] = []
    for row in rows:
        schema_name, table_name, geom_col, _dim, srid, gtype = row
        full_name = f"{schema_name}.{table_name}" if schema_name != "public" else table_name
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """,
            (schema_name, table_name),
        )
        columns = [r[0] for r in cur.fetchall()]
        tables.append(
            TableMeta(
                name=full_name,
                geom_column=geom_col,
                geom_type=gtype or "GEOMETRY",
                srid=int(srid) if srid is not None else 0,
                columns=columns,
            )
        )
    cur.close()
    return Schema(tables=tables)
