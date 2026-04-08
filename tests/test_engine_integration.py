"""Live LLM calls (requires API keys)."""

from __future__ import annotations

import os

import pytest

from geointent.engine import Engine
from geointent.types import Dialect


@pytest.mark.live
def test_e2e_manhole_query_postgis(utility_context):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    eng = Engine(llm="claude", context=utility_context)
    result = eng.translate("manholes within 50 feet of a gas line", dialect=Dialect.POSTGIS)
    assert "ST_DWithin" in result.query
    assert result.confidence > 0.7
