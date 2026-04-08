"""Intent parsing: LLM (or mock) output plus resolver merge."""

from __future__ import annotations

from typing import Any, Protocol

from geointent.compiler.resolver import terms as term_resolvers
from geointent.types import IntentResult, SpatialContext


class IntentBackend(Protocol):
    def complete_intent(self, nl: str, context: SpatialContext) -> IntentResult: ...


def merge_resolver_into_intent(
    intent: IntentResult, context: SpatialContext
) -> tuple[IntentResult, bool]:
    """
    When the LLM omits distance for buffer predicates, fill from domain resolver.
    Returns (intent, used_resolver).
    """
    pred = intent.predicate.upper()
    if "DWITHIN" in pred and (intent.distance is None) and intent.ref_table:
        resolved = term_resolvers.resolve_near(context)
        if resolved.distance_meters is not None:
            merged = intent.model_copy(
                update={
                    "distance": resolved.distance_meters,
                    "distance_unit": "meters",
                    "assumptions": {
                        **intent.assumptions,
                        "near": resolved.assumption,
                    },
                }
            )
            return merged, True
    return intent, False


def compute_confidence(intent: IntentResult, used_resolver: bool) -> float:
    base = 0.75
    if intent.subject_table and (intent.ref_table or "WITHIN" in intent.predicate.upper()):
        base += 0.1
    if used_resolver:
        base += 0.05
    return min(0.95, base)


def build_alternate_intents(base: IntentResult, context: SpatialContext) -> list[IntentResult]:
    """Up to 2 alternate interpretations with different distance multipliers."""
    if base.distance is None or base.ref_table is None:
        return []
    try:
        m = term_resolvers.distance_from_intent_to_meters(base.distance, base.distance_unit)
    except ValueError:
        return []
    if m is None:
        return []
    alts: list[IntentResult] = []
    for mult, label in ((0.5, "tighter"), (2.0, "broader")):
        alts.append(
            base.model_copy(
                update={
                    "distance": m * mult,
                    "distance_unit": "meters",
                    "assumptions": {
                        **base.assumptions,
                        "buffer_variant": f"{label} ({mult}x)",
                    },
                }
            )
        )
        if len(alts) >= 2:
            break
    return alts[:2]
