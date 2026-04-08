"""OpenAI Chat Completions backend — JSON mode, retries."""

from __future__ import annotations

import json
import os
import random
import time
from typing import Any

from geointent.types import LLMError

DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIBackend:
    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.environ.get("NLGEO_OPENAI_MODEL", DEFAULT_MODEL)

    def complete_json(self, system_prompt: str, user_message: str) -> dict[str, Any]:
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                return self._call(system_prompt, user_message)
            except Exception as e:
                last_err = e
                if attempt < 2:
                    time.sleep((2**attempt) + random.random())
                continue
        raise LLMError(f"OpenAI backend failed after retries: {last_err!r}") from last_err

    def _call(self, system_prompt: str, user_message: str) -> dict[str, Any]:
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise LLMError("OPENAI_API_KEY is not set")
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        content = resp.choices[0].message.content or "{}"
        return json.loads(content)
