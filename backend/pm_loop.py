"""PM loop skeleton (Issue #15).

Runs locally, checks for new feedback since last run, and if present:
- writes a daily plan markdown under docs/daily/
- inserts a changelog entry
- records a run in pm_runs

No LLM calls yet: plan is a structured placeholder derived from feedback counts.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from db import get_conn, init_db


REPO_ROOT = Path(__file__).resolve().parent.parent
DAILY_DIR = REPO_ROOT / "docs" / "daily"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def latest_run_finished_at() -> str | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT finished_at FROM pm_runs WHERE finished_at IS NOT NULL ORDER BY finished_at DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else None


def count_new_feedback(since_iso: str | None) -> int:
    with get_conn() as conn:
        if since_iso is None:
            a = conn.execute("SELECT COUNT(*) FROM answer_feedback").fetchone()[0]
            f = conn.execute("SELECT COUNT(*) FROM freeform_feedback").fetchone()[0]
        else:
            a = conn.execute(
                "SELECT COUNT(*) FROM answer_feedback WHERE created_at > ?", (since_iso,)
            ).fetchone()[0]
            f = conn.execute(
                "SELECT COUNT(*) FROM freeform_feedback WHERE created_at > ?", (since_iso,)
            ).fetchone()[0]
    return int(a) + int(f)


def write_daily_plan(feedback_count: int) -> Path:
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = DAILY_DIR / f"{day}-plan.md"

    content = f"""# Daily Plan ({day})\n\n## Input\n- New feedback items since last run: **{feedback_count}**\n\n## Proposed work (placeholder)\n- Review new feedback\n- Pick top 1-3 items\n- Draft plan/spec\n- Implement (future)\n- Validate + update changelog\n\n## Notes\nThis is a skeleton plan. Next step: replace placeholder logic with an agent summarizer + GitHub issue triage.\n"""
    path.write_text(content)
    return path


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


def main() -> int:
    init_db()

    started_at = now_iso()
    since = latest_run_finished_at()
    new_count = count_new_feedback(since)

    if new_count <= 0:
        record_run(started_at, now_iso(), "skipped", 0, "No new feedback")
        return 0

    plan_path = write_daily_plan(new_count)
    chg_id = insert_changelog_entry(
        title="Nightly PM loop ran",
        body_md=f"Generated plan: `{plan_path.relative_to(REPO_ROOT)}`\n\nNew feedback count: **{new_count}**\n\nChangelog id: (this entry)",
    )

    record_run(started_at, now_iso(), "ok", new_count, f"plan={plan_path} changelog={chg_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
