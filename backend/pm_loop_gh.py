"""PM loop v1: turn feedback into GitHub Issues (Issue #24).

Design:
- Uses local SQLite feedback tables.
- If no new feedback since last run -> skip.
- Otherwise:
  - write docs/daily/YYYY-MM-DD-plan.md
  - create GitHub issues via `gh issue create`
  - insert a changelog entry containing created issue URLs

Requires:
- `gh auth status` configured
- repo env var: GITHUB_REPO (default: ninjapapa/chatui)

Notes:
- This script is intentionally simple and deterministic.
- Later: use LLM summarization + dedupe + labeling.
"""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from db import get_conn, init_db

REPO_ROOT = Path(__file__).resolve().parent.parent
DAILY_DIR = REPO_ROOT / "docs" / "daily"
GITHUB_REPO = os.environ.get("GITHUB_REPO", "ninjapapa/chatui")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def latest_run_finished_at() -> str | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT finished_at FROM pm_runs WHERE finished_at IS NOT NULL ORDER BY finished_at DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else None


def fetch_new_feedback(since_iso: str | None, limit: int = 50) -> list[dict]:
    with get_conn() as conn:
        if since_iso is None:
            ans = conn.execute(
                """
                SELECT id, chat_id, message_id, thumbs, comment, created_at
                FROM answer_feedback
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            free = conn.execute(
                """
                SELECT id, chat_id, text, created_at, metadata_json
                FROM freeform_feedback
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        else:
            ans = conn.execute(
                """
                SELECT id, chat_id, message_id, thumbs, comment, created_at
                FROM answer_feedback
                WHERE created_at > ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (since_iso, limit),
            ).fetchall()
            free = conn.execute(
                """
                SELECT id, chat_id, text, created_at, metadata_json
                FROM freeform_feedback
                WHERE created_at > ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (since_iso, limit),
            ).fetchall()

    out: list[dict] = []
    for r in ans:
        out.append(
            {
                "kind": "answer_feedback",
                "id": r[0],
                "chat_id": r[1],
                "message_id": r[2],
                "thumbs": r[3],
                "comment": r[4],
                "created_at": r[5],
            }
        )
    for r in free:
        meta = None
        if r[4]:
            try:
                meta = json.loads(r[4])
            except Exception:
                meta = None
        out.append(
            {
                "kind": "freeform_feedback",
                "id": r[0],
                "chat_id": r[1],
                "text": r[2],
                "created_at": r[3],
                "metadata": meta,
            }
        )

    # newest-first
    out.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return out


def _gh_list_labels() -> set[str]:
    """Return repo labels (lowercased names)."""
    try:
        res = subprocess.run(
            ["gh", "label", "list", "-R", GITHUB_REPO, "--limit", "200"],
            check=True, capture_output=True, text=True,
        )
    except Exception:
        return set()

    out: set[str] = set()
    for line in (res.stdout or "").splitlines():
        # format: <name>	<description>	<color> (or similar)
        name = (line.split("	", 1)[0] if "	" in line else line.split(" ", 1)[0]).strip()
        if name:
            out.add(name.lower())
    return out


def _safe_labels(requested: list[str] | None) -> list[str] | None:
    if not requested:
        return None
    avail = _gh_list_labels()
    if not avail:
        # If we can't list labels, be conservative and don't pass any.
        return None

    filtered = [l for l in requested if l.lower() in avail]
    return filtered or None


def gh_issue_create(title: str, body: str, labels: list[str] | None = None) -> str:
    cmd = ["gh", "issue", "create", "-R", GITHUB_REPO, "--title", title, "--body", body]
    safe = _safe_labels(labels)
    if safe:
        for l in safe:
            cmd.extend(["--label", l])

    res = subprocess.run(cmd, check=True, capture_output=True, text=True)
    # gh prints the URL on stdout
    url = res.stdout.strip().splitlines()[-1]
    return url


def insert_changelog_entry(title: str, body_md: str) -> str:
    entry_id = f"chg_{uuid.uuid4().hex}"
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO changelog_entries(id, title, body_md, created_at) VALUES (?, ?, ?, ?)",
            (entry_id, title, body_md, now_iso()),
        )
    return entry_id


def record_run(started_at: str, finished_at: str | None, status: str, new_feedback_count: int, notes: str | None):
    run_id = f"pm_{uuid.uuid4().hex}"
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO pm_runs(id, started_at, finished_at, status, new_feedback_count, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, started_at, finished_at, status, int(new_feedback_count), notes),
        )


def write_daily_plan(items: list[dict], created_issue_urls: list[str]) -> Path:
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = DAILY_DIR / f"{day}-plan.md"

    lines: list[str] = []
    lines.append(f"# Daily Plan ({day})")
    lines.append("")
    lines.append("## New feedback")
    lines.append(f"Count: **{len(items)}**")
    lines.append("")

    for it in items[:20]:
        if it["kind"] == "answer_feedback":
            lines.append(f"- answer_feedback {it['id']} thumbs={it['thumbs']} comment={it.get('comment')!r}")
        else:
            t = (it.get("text") or "").replace("\n", " ")
            lines.append(f"- freeform {it['id']}: {t[:160]}")

    lines.append("")
    lines.append("## Created GitHub issues")
    if created_issue_urls:
        for url in created_issue_urls:
            lines.append(f"- {url}")
    else:
        lines.append("- (none)")

    lines.append("")
    lines.append("## Next steps")
    lines.append("- Review created issues")
    lines.append("- Prioritize top 1-3 items")
    lines.append("- Implement + regression")

    path.write_text("\n".join(lines) + "\n")
    return path


def main() -> int:
    init_db()

    started_at = now_iso()
    since = latest_run_finished_at()
    items = fetch_new_feedback(since)

    if not items:
        record_run(started_at, now_iso(), "skipped", 0, "No new feedback")
        return 0

    created_urls: list[str] = []

    # Create issues for freeform feature requests; otherwise just aggregate.
    for it in items:
        if it["kind"] != "freeform_feedback":
            continue
        meta = it.get("metadata") or {}
        if meta.get("type") == "feature_request":
            title = meta.get("title") or "Feature request"
            body = it.get("text") or ""
            url = gh_issue_create(title=str(title), body=str(body), labels=["feedback", "feature"])
            created_urls.append(url)

    plan_path = write_daily_plan(items, created_urls)

    insert_changelog_entry(
        title="PM loop: feedback triage",
        body_md=(
            f"Generated plan: `{plan_path.relative_to(REPO_ROOT)}`\n\n"
            + ("Created issues:\n" + "\n".join(f"- {u}" for u in created_urls) if created_urls else "Created issues: (none)")
        ),
    )

    record_run(started_at, now_iso(), "ok", len(items), f"created={len(created_urls)} plan={plan_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
