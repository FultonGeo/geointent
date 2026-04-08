"""Deterministic mock LLM for unit tests — keyed by natural language input."""

from __future__ import annotations

from typing import Any

from nlgeo.types import IntentResult, SpatialContext


class MockLLMBackend:
    def __init__(self, responses: dict[str, IntentResult] | None = None) -> None:
        self._responses: dict[str, IntentResult] = responses or {}

    def set_response(self, nl: str, intent: IntentResult) -> None:
        self._responses[nl.strip()] = intent

    def complete_intent(self, nl: str, context: SpatialContext) -> IntentResult:
        key = nl.strip()
        if key not in self._responses:
            raise KeyError(f"MockLLMBackend: no canned response for {key!r}")
        return self._responses[key]
