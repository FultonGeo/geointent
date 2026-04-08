"""System prompt assembly for structured IntentResult JSON."""

from __future__ import annotations

import json

from nlgeo.compiler.resolver import domains
from nlgeo.types import SpatialContext


def build_system_prompt(ctx: SpatialContext) -> str:
    schema_json = ctx.schema.to_prompt_str()
    thresh_json = json.dumps(domains.threshold_tables(), separators=(",", ":"))
    return (
        "You are a spatial query compiler. Reply with a single JSON object only, no markdown, "
        "matching this schema:\n"
        '{ "predicate": string (e.g. ST_DWithin, ST_Within, ST_Contains), '
        '"subject_table": string, "ref_table": string|null, '
        '"distance": number|null, "distance_unit": string|null, '
        '"filters": object, "assumptions": object }\n'
        f"Spatial context: domain={ctx.domain!r}, units={ctx.units!r}, srid={ctx.srid}, "
        f"bbox={ctx.bbox!r}.\n"
        f"Schema (tables and geometry columns): {schema_json}\n"
        f"Domain default distances (meters) by term: {thresh_json}\n"
        "Use exact table and column names from the schema. Prefer ST_DWithin for proximity.\n"
        'You may optionally add "alternatives": [ { same shape as root fields, different distance } ] '
        "with up to 2 variants (e.g. tighter/broader buffer); omit if not needed."
    )
