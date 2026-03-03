from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Any

import requests

from db import get_conn


@dataclass
class RetrievedDoc:
    url: str
    title: str | None
    text: str


BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY")
BRAVE_ENDPOINT = os.environ.get("BRAVE_SEARCH_ENDPOINT", "https://api.search.brave.com/res/v1/web/search")


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def init_retrieval_tables() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS source_cache (
              url TEXT PRIMARY KEY,
              url_hash TEXT NOT NULL,
              title TEXT,
              fetched_at TEXT NOT NULL,
              content_text TEXT NOT NULL
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_source_cache_hash ON source_cache(url_hash);")


def cached_get(url: str, max_chars: int = 20_000) -> RetrievedDoc | None:
    """Fetch a URL and cache it in SQLite.

    Cache key is the URL.
    """
    init_retrieval_tables()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT url, title, content_text FROM source_cache WHERE url = ?",
            (url,),
        ).fetchone()
        if row:
            return RetrievedDoc(url=row[0], title=row[1], text=row[2])

    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "chatui/0.1"})
        r.raise_for_status()
        text = r.text
    except Exception:
        return None

    # crude HTML->text: strip tags by removing everything between <...>
    # (good enough for MVP; can replace with readability later)
    import re

    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if max_chars and len(text) > max_chars:
        text = text[:max_chars]

    fetched_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO source_cache(url, url_hash, title, fetched_at, content_text) VALUES (?, ?, ?, ?, ?)",
            (url, _sha256(url), None, fetched_at, text),
        )

    return RetrievedDoc(url=url, title=None, text=text)


def brave_search(query: str, count: int = 5) -> list[dict[str, Any]]:
    if not BRAVE_API_KEY:
        return []

    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY,
        "User-Agent": "chatui/0.1",
    }
    params = {"q": query, "count": str(count)}

    r = requests.get(BRAVE_ENDPOINT, headers=headers, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    # Brave schema: web.results[*] typically includes url/title/description
    results = (((data or {}).get("web") or {}).get("results")) or []
    out: list[dict[str, Any]] = []
    for it in results[:count]:
        url = it.get("url")
        if not url:
            continue
        out.append(
            {
                "url": url,
                "title": it.get("title"),
                "description": it.get("description"),
            }
        )
    return out


def retrieve(query: str, count: int = 5) -> list[RetrievedDoc]:
    """Search (if configured) then fetch/cache top results."""
    results = brave_search(query, count=count)
    docs: list[RetrievedDoc] = []

    for r in results:
        url = r.get("url")
        if not url:
            continue
        doc = cached_get(url)
        if doc:
            docs.append(doc)

    return docs
