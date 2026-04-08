"""OpenAI backend — same complete_json contract as Claude (mocked)."""

from __future__ import annotations

import pytest

from geointent.llm.backends.openai import OpenAIBackend
from geointent.types import IntentResult, LLMError


def _sample():
    return {
        "predicate": "ST_Within",
        "subject_table": "parcels",
        "ref_table": "flood_zones",
        "distance": None,
        "distance_unit": None,
        "filters": {},
        "assumptions": {},
    }


def test_openai_backend_complete_json(monkeypatch):
    b = OpenAIBackend()
    monkeypatch.setattr(b, "_call", lambda _s, _u: _sample())
    d = b.complete_json("sys", "user")
    assert IntentResult.model_validate(d).subject_table == "parcels"


def test_openai_backend_retries(monkeypatch):
    b = OpenAIBackend()
    n = {"c": 0}

    def flaky(_s, _u):
        n["c"] += 1
        if n["c"] < 3:
            raise ConnectionError("reset")
        return _sample()

    monkeypatch.setattr(b, "_call", flaky)
    b.complete_json("", "")
    assert n["c"] == 3


def test_openai_backend_llm_error_after_retries(monkeypatch):
    b = OpenAIBackend()
    monkeypatch.setattr(b, "_call", lambda _s, _u: (_ for _ in ()).throw(ValueError("x")))
    with pytest.raises(LLMError):
        b.complete_json("", "")
