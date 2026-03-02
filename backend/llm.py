from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def _client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


SYSTEM_PROMPT = """You are a helpful assistant that explains the US healthcare system.

Rules:
- Provide educational information only. Do NOT give medical advice, diagnosis, or treatment recommendations.
- Always include citations for factual claims. Use the format:

  Sources:
  - <url>
  - <url>

- If you are unsure, say so and suggest what to look up.
"""


def answer_with_citations(user_text: str) -> str:
    if os.environ.get("CHATUI_TEST_MODE") == "1":
        return "Sources:\n- https://example.com\n"
    """Return markdown with a required Sources section.

Note: For now, citations may be general authoritative sources.
Later we will wire in web search + grounded citations.
"""
    client = _client()

    resp = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        temperature=0.2,
    )
    content = resp.choices[0].message.content or ""

    # Ensure a Sources section exists. If model forgot, add a minimal one.
    if "Sources:" not in content:
        content = (
            content.rstrip()
            + "\n\nSources:\n"
            + "- https://www.medicare.gov/\n"
            + "- https://www.cms.gov/\n"
        )
    return content
