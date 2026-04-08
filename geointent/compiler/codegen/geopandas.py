"""GeoPandas / Shapely codegen from IntentResult."""

from __future__ import annotations

from geointent.types import IntentResult, SpatialContext
from geointent.units import to_meters


def render_intent(intent: IntentResult, ctx: SpatialContext) -> str:
    """Executable Python using geopandas and shapely only."""
    subj = intent.subject_table
    ref = intent.ref_table
    pred_u = intent.predicate.upper()

    if ref is None:
        raise ValueError("GeoPandas codegen requires ref_table for spatial relation")

    lines = [
        "import geopandas as gpd",
        "from shapely.ops import unary_union",
        "",
        f'{subj}_gdf = gpd.read_postgis(\'SELECT * FROM "{subj}"\', conn, geom_col="geom")',
        f'{ref}_gdf = gpd.read_postgis(\'SELECT * FROM "{ref}"\', conn, geom_col="geom")',
    ]

    if "DWITHIN" in pred_u:
        if intent.distance is None:
            raise ValueError("near/ST_DWithin requires distance")
        unit = intent.distance_unit or "meters"
        dist_m = to_meters(float(intent.distance), unit)
        lines += [
            f"ref_union = unary_union({ref}_gdf.geometry)",
            f"near_mask = {subj}_gdf.geometry.buffer({dist_m}).intersects(ref_union)",
            f"result_gdf = {subj}_gdf.loc[near_mask].copy()",
        ]
    elif "WITHIN" in pred_u and "DWITHIN" not in pred_u:
        lines += [
            f"ref_union = unary_union({ref}_gdf.geometry)",
            f"result_gdf = {subj}_gdf[{subj}_gdf.geometry.within(ref_union)].copy()",
        ]
    else:
        lines.append(f"# predicate {intent.predicate!r} — extend geopandas renderer")

    lines.append("result_gdf")
    return "\n".join(lines)
