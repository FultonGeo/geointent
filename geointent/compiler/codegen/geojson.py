"""GeoJSON filter expression (RFC 7946-style) from IntentResult."""

from __future__ import annotations

import json

from geointent.types import IntentResult, SpatialContext
from geointent.units import to_meters


def render_intent(intent: IntentResult, ctx: SpatialContext) -> str:
    """Return a JSON string for a simple spatial filter structure."""
    pred_u = intent.predicate.upper()
    ref = intent.ref_table
    payload: dict[str, object] = {
        "op": "spatial",
        "subject": intent.subject_table,
        "reference": ref,
        "predicate": intent.predicate,
    }
    if "DWITHIN" in pred_u and intent.distance is not None:
        unit = intent.distance_unit or "meters"
        dist_m = to_meters(float(intent.distance), unit)
        payload["distance_m"] = dist_m
    return json.dumps(payload, separators=(",", ":"))
