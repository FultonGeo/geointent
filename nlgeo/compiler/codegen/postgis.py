"""PostGIS SQL generation from IntentResult — parameterized, SRID-aware."""

from __future__ import annotations

from typing import Any

from nlgeo.types import IntentResult, SpatialContext
from nlgeo.units import to_meters


def _meters_to_crs_distance(distance_m: float, ctx: SpatialContext) -> tuple[float, str | None]:
    """
    ST_DWithin for geometry uses CRS units: meters for projected, degrees for lon/lat.
    Returns (value_for_placeholder, optional_comment).
    """
    srid = ctx.srid
    if srid == 4326:
        deg = distance_m / 111320.0
        return deg, (
            f"distance converted from {distance_m:.2f}m to ~{deg:.8f} deg for SRID 4326 geometry"
        )
    return distance_m, None


def _normalize_distance_to_meters(intent: IntentResult) -> float | None:
    if intent.distance is None:
        return None
    unit = intent.distance_unit or "meters"
    return to_meters(float(intent.distance), unit)


def render_intent(intent: IntentResult, ctx: SpatialContext) -> tuple[str, list[Any]]:
    """
    Return (sql, params) for parameterized execution.
    Uses %s placeholders for all dynamic values.
    """
    subj = intent.subject_table
    ref = intent.ref_table
    subj_alias, ref_alias = "s", "r"
    params: list[Any] = []
    comment_lines: list[str] = []

    pred_u = intent.predicate.upper().replace(" ", "_")

    if "DWITHIN" in pred_u:
        distance_m = _normalize_distance_to_meters(intent)
        if ref is None or distance_m is None:
            raise ValueError("ST_DWithin requires ref_table and distance")
        d_val, conv_note = _meters_to_crs_distance(distance_m, ctx)
        if conv_note:
            comment_lines.append(f"-- {conv_note}")
        params.append(d_val)
        sql_core = (
            f'SELECT {subj_alias}.* FROM "{subj}" AS {subj_alias} '
            f'INNER JOIN "{ref}" AS {ref_alias} ON ST_DWithin('
            f"{subj_alias}.geom, {ref_alias}.geom, %s)"
        )
    elif "CONTAINS" in pred_u:
        if ref is None:
            raise ValueError("ST_Contains requires ref_table")
        sql_core = (
            f'SELECT {subj_alias}.* FROM "{subj}" AS {subj_alias} '
            f'INNER JOIN "{ref}" AS {ref_alias} ON ST_Contains('
            f"{ref_alias}.geom, {subj_alias}.geom)"
        )
    elif "WITHIN" in pred_u and "DWITHIN" not in pred_u:
        if ref is None:
            raise ValueError("ST_Within requires ref_table")
        sql_core = (
            f'SELECT {subj_alias}.* FROM "{subj}" AS {subj_alias} '
            f'INNER JOIN "{ref}" AS {ref_alias} ON ST_Within('
            f"{subj_alias}.geom, {ref_alias}.geom)"
        )
    else:
        raise ValueError(f"Unsupported predicate for PostGIS: {intent.predicate}")

    where_parts: list[str] = []
    for key, val in intent.filters.items():
        if key == "last_inspection_before":
            params.append(str(val))
            where_parts.append(f"{subj_alias}.last_inspection < %s::date")
        elif key == "last_inspection_after":
            params.append(str(val))
            where_parts.append(f"{subj_alias}.last_inspection > %s::date")
        else:
            params.append(val)
            where_parts.append(f"{subj_alias}.{key} = %s")

    lines = comment_lines + [sql_core]
    if where_parts:
        lines.append("WHERE " + " AND ".join(where_parts))
    sql = "\n".join(lines) + ";"
    return sql, params


def render_intent_sql_string(intent: IntentResult, ctx: SpatialContext) -> str:
    sql, _params = render_intent(intent, ctx)
    return sql
