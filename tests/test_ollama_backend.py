"""Ollama backend — same complete_json contract and retry behavior (mocked _call)."""

from __future__ import annotations

import pytest

from geointent.llm.backends.ollama import OllamaBackend
from geointent.types import LLMError


def _sample():
    return {
        "predicate": "ST_DWithin",
        "subject_table": "buildings",
        "ref_table": "roads",
        "distance": 100.0,
        "distance_unit": "meters",
        "filters": {},
        "assumptions": {},
    }


def test_ollama_backend_complete_json(monkeypatch):
    b = OllamaBackend()
    monkeypatch.setattr(b, "_call", lambda _s, _u: _sample())
    d = b.complete_json("sys", "user")
    assert d["subject_table"] == "buildings"


def test_ollama_backend_retries(monkeypatch):
    b = OllamaBackend()
    calls = {"n": 0}

    def flaky(_s, _u):
        calls["n"] += 1
        if calls["n"] < 2:
            raise ConnectionError("refused")
        return _sample()

    monkeypatch.setattr(b, "_call", flaky)
    b.complete_json("", "")
    assert calls["n"] == 2


def test_ollama_backend_llm_error(monkeypatch):
    b = OllamaBackend()

    def boom(_s, _u):
        raise RuntimeError("always")

    monkeypatch.setattr(b, "_call", boom)
    with pytest.raises(LLMError):
        b.complete_json("", "")
