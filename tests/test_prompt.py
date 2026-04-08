"""LLM system prompt assembly."""

from __future__ import annotations

from geointent.llm import prompt


def test_prompt_contains_schema(utility_context):
    p = prompt.build_system_prompt(utility_context)
    assert "gas_lines" in p
    assert "manholes" in p
    assert "geom_column" in p or "geom" in p


def test_prompt_contains_domain(utility_context):
    p = prompt.build_system_prompt(utility_context)
    assert "utility_network" in p
