"""Anthropic Claude backend — JSON output, retries, exponential backoff."""

from __future__ import annotations

import json
import os
import random
import time
from typing import Any

from nlgeo.types import LLMError

DEFAULT_MODEL = "claude-3-5-sonnet-20241022"


class ClaudeBackend:
    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.environ.get("NLGEO_CLAUDE_MODEL", DEFAULT_MODEL)

    def complete_json(self, system_prompt: str, user_message: str) -> dict[str, Any]:
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                return self._call(system_prompt, user_message)
            except Exception as e:
                last_err = e
                if attempt < 2:
                    delay = (2**attempt) + random.random()
                    time.sleep(delay)
                continue
        raise LLMError(f"Claude backend failed after retries: {last_err!r}") from last_err

    def _call(self, system_prompt: str, user_message: str) -> dict[str, Any]:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY is not set")
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        text = ""
        for block in msg.content:
            if block.type == "text":
                text += block.text
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        data = json.loads(text)
        return data
