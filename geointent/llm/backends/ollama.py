"""Ollama local HTTP backend — JSON output, retries."""

from __future__ import annotations

import json
import os
import random
import time
from typing import Any

import httpx

from geointent.types import LLMError

DEFAULT_BASE = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2"


class OllamaBackend:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or os.environ.get("OLLAMA_HOST", DEFAULT_BASE)).rstrip("/")
        self.model = model or os.environ.get("NLGEO_OLLAMA_MODEL", DEFAULT_MODEL)

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
        raise LLMError(f"Ollama backend failed after retries: {last_err!r}") from last_err

    def _call(self, system_prompt: str, user_message: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        }
        with httpx.Client(timeout=120.0) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
        text = (data.get("message") or {}).get("content") or "{}"
        return json.loads(text)
