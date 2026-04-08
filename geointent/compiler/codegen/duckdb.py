"""DuckDB spatial SQL — Overture-style bbox pruning + ST_DWithin."""

from __future__ import annotations

from geointent.types import IntentResult, SpatialContext
from geointent.units import to_meters


def render_intent(intent: IntentResult, ctx: SpatialContext) -> str:
    """Generate DuckDB SQL with bbox filter and spatial predicate."""
    subj = intent.subject_table
    ref = intent.ref_table or subj
    bbox = ctx.bbox
    bbox_sql = ""
    if bbox is not None:
        xmin, ymin, xmax, ymax = bbox
        bbox_sql = (
            f" AND bbox.xmin >= {xmin} AND bbox.xmax <= {xmax}"
            f" AND bbox.ymin >= {ymin} AND bbox.ymax <= {ymax}"
        )

    pred_u = intent.predicate.upper()
    if "DWITHIN" in pred_u and intent.distance is not None:
        unit = intent.distance_unit or "meters"
        dist_m = to_meters(float(intent.distance), unit)
        return (
            f'SELECT s.* FROM "{subj}" s JOIN "{ref}" r ON ST_DWithin(s.geometry, r.geometry, {dist_m})'
            f" WHERE 1=1{bbox_sql};"
        )
    return (
        f'SELECT * FROM "{subj}" WHERE 1=1{bbox_sql};'
    )
