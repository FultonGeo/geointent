"""Claude backend unit tests (mocked API, no network)."""

from __future__ import annotations

import pytest

from nlgeo.llm.backends.claude import ClaudeBackend
from nlgeo.types import IntentResult, LLMError


def _sample_intent_dict():
    return {
        "predicate": "ST_DWithin",
        "subject_table": "manholes",
        "ref_table": "gas_lines",
        "distance": 50.0,
        "distance_unit": "feet",
        "filters": {},
        "assumptions": {},
    }


def test_claude_backend_parses_valid_json(monkeypatch):
    backend = ClaudeBackend()
    monkeypatch.setattr(backend, "_call", lambda _s, _u: _sample_intent_dict())
    out = backend.complete_json("system", "user")
    intent = IntentResult.model_validate(out)
    assert intent.subject_table == "manholes"


def test_claude_backend_retries_on_failure(monkeypatch):
    backend = ClaudeBackend()
    calls = {"n": 0}

    def flaky(_s, _u):
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("transient")
        return _sample_intent_dict()

    monkeypatch.setattr(backend, "_call", flaky)
    out = backend.complete_json("system", "user")
    assert out["subject_table"] == "manholes"
    assert calls["n"] == 2


def test_claude_backend_raises_after_max_retries(monkeypatch):
    backend = ClaudeBackend()

    def fail(_s, _u):
        raise RuntimeError("fail")

    monkeypatch.setattr(backend, "_call", fail)
    with pytest.raises(LLMError, match="fail"):
        backend.complete_json("system", "user")
