"""PM loop v3: triage feedback -> (optionally) implement issues.

This script supports two modes:

1) triage (default)
   - fetch new feedback since last pm_runs.finished_at
   - fetch recent GitHub issues (for dedupe context)
   - call an OpenClaw agent to analyze/dedupe and propose issue drafts
   - create GitHub issues via `gh issue create`
   - write docs/daily/YYYY-MM-DD-plan.md
   - insert a changelog entry containing created issue URLs

2) apply (new)
   - fetch a specific GitHub issue
   - call an OpenClaw agent to implement it in the repo working tree (no commit)
   - run tests
   - commit + push
   - relaunch/restart local services via an optional hook

Requires:
- `gh auth status` configured
- OpenClaw gateway running (or embedded fallback)

Config (env vars):
- GITHUB_REPO: default ninjapapa/chatui
- PM_AGENT_ID: OpenClaw agent id to use (default chatui-pm)
- PM_TEST_CMD: default "npm test"
- PM_RELAUNCH_CMD: optional shell command to relaunch services after push

Notes:
- The OpenClaw agent MUST return JSON only for machine parsing.
- The agent is expected to modify files but NOT commit/push.
"""

from __future__ import annotations

import argparse
import json
import re
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from db import get_conn, init_db

REPO_ROOT = Path(__file__).resolve().parent.parent
DAILY_DIR = REPO_ROOT / "docs" / "daily"

GITHUB_REPO = os.environ.get("GITHUB_REPO", "ninjapapa/chatui")
PM_AGENT_ID = os.environ.get("PM_AGENT_ID", "chatui-pm")
PM_TEST_CMD = os.environ.get("PM_TEST_CMD", "npm test")
PM_RELAUNCH_CMD = os.environ.get("PM_RELAUNCH_CMD")


def _run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=str(cwd) if cwd else None)


def _run_shell(command: str, *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    # bash -lc so user env/rc can apply when needed
    return _run(["bash", "-lc", command], cwd=cwd)


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


def fetch_recent_github_issues(limit: int = 200) -> list[dict]:
    """Fetch recent issues for dedupe. Best-effort; returns [] on failure."""
    try:
        res = _run(
            [
                "gh",
                "issue",
                "list",
                "-R",
                GITHUB_REPO,
                "--limit",
                str(limit),
                "--state",
                "all",
                "--json",
                "number,title,url,state,labels,createdAt",
            ],
            cwd=REPO_ROOT,
        )
        return json.loads(res.stdout or "[]")
    except Exception:
        return []


def gh_issue_view(issue: str) -> dict:
    """View a GitHub issue by number or URL."""
    res = _run(
        [
            "gh",
            "issue",
            "view",
            issue,
            "-R",
            GITHUB_REPO,
            "--json",
            "number,title,url,body,state,labels,assignees,createdAt",
        ],
        cwd=REPO_ROOT,
    )
    return json.loads(res.stdout or "{}")


def _gh_list_labels() -> set[str]:
    """Return repo labels (lowercased names)."""
    try:
        res = _run(["gh", "label", "list", "-R", GITHUB_REPO, "--limit", "200"], cwd=REPO_ROOT)
    except Exception:
        return set()

    out: set[str] = set()
    for line in (res.stdout or "").splitlines():
        # format: <name>\t<description>\t<color> (or similar)
        name = (line.split("\t", 1)[0] if "\t" in line else line.split(" ", 1)[0]).strip()
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

    res = _run(cmd, cwd=REPO_ROOT)
    # gh prints the URL on stdout
    url = (res.stdout or "").strip().splitlines()[-1]
    return url


def insert_changelog_entry(title: str, body_md: str) -> str:
    entry_id = f"chg_{uuid.uuid4().hex}"
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO changelog_entries(id, title, body_md, created_at) VALUES (?, ?, ?, ?)",
            (entry_id, title, body_md, now_iso()),
        )
    return entry_id


def record_run(
    started_at: str,
    finished_at: str | None,
    status: str,
    new_feedback_count: int,
    notes: str | None,
):
    run_id = f"pm_{uuid.uuid4().hex}"
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO pm_runs(id, started_at, finished_at, status, new_feedback_count, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, started_at, finished_at, status, int(new_feedback_count), notes),
        )


def _parse_json_payload_from_openclaw(outer: dict) -> dict:
    """Extract and parse the assistant JSON response from an openclaw agent --json run.

    OpenClaw returns an outer JSON envelope. The assistant response text is in result.payloads[].text.
    Some models may include extra whitespace or preambles; we attempt best-effort JSON block extraction.
    """

    payloads = (((outer.get("result") or {}).get("payloads")) or [])
    texts = [str(p.get("text") or "").strip() for p in payloads if (p.get("text") or "").strip()]
    if not texts:
        raise RuntimeError("OpenClaw returned no text payloads")

    raw = texts[-1]

    try:
        return json.loads(raw)
    except Exception:
        # Best-effort: extract first JSON object/array from the text.
        m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", raw)
        if not m:
            raise RuntimeError(f"OpenClaw returned non-JSON response: {raw[:400]!r}")
        blob = m.group(1)
        return json.loads(blob)


def openclaw_analyze(items: list[dict], existing_issues: list[dict]) -> dict:
    """Call OpenClaw agent to propose issue drafts + dedupe decisions."""

    payload = {
        "github_repo": GITHUB_REPO,
        "new_feedback": items,
        "existing_issues": existing_issues,
        "instructions": {
            "goal": "Create GitHub issue drafts from new user feedback, deduping against existing issues.",
            "output": "Return JSON only. No markdown, no commentary.",
            "max_proposals": 20,
            "prefer_feature_requests": True,
        },
    }

    prompt = (
        "You are the ChatUI PM assistant.\n"
        "Analyze the provided feedback and existing GitHub issues.\n"
        "Return JSON ONLY with shape: {\"proposals\":[...]}\n\n"
        "Rules:\n"
        "- Deduplicate: if an existing issue already covers it, set action=\"skip_duplicate\" and duplicate_of=<url>.\n"
        "- Otherwise action=\"create\" with a concise title and a short markdown body.\n"
        "- Keep it simple: title + body + optional labels.\n"
        "- Prefer creating issues only for freeform_feedback where metadata.type == feature_request (but you may include other high-signal items).\n"
        "- Do NOT include anything except valid JSON in the response.\n\n"
        "INPUT_JSON:\n"
        + json.dumps(payload, ensure_ascii=False)
    )

    run = _run(
        [
            "openclaw",
            "agent",
            "--agent",
            PM_AGENT_ID,
            "--thinking",
            "low",
            "--json",
            "--timeout",
            "600",
            "--message",
            prompt,
        ],
        cwd=REPO_ROOT,
    )

    outer = json.loads(run.stdout or "{}")
    return _parse_json_payload_from_openclaw(outer)


def openclaw_apply_issue(issue: dict) -> dict:
    """Ask OpenClaw agent to implement a GitHub issue in the repo working tree.

    The agent must:
    - make code changes locally
    - run fast checks if helpful
    - NOT commit or push
    - return JSON only with a short summary

    Expected JSON (loose):
    {"ok": true, "summary": "...", "notes": "..."}
    """

    payload = {
        "github_repo": GITHUB_REPO,
        "issue": {
            "number": issue.get("number"),
            "title": issue.get("title"),
            "url": issue.get("url"),
            "body": issue.get("body"),
        },
        "repo_root": str(REPO_ROOT),
        "instructions": {
            "do_not_commit": True,
            "do_not_push": True,
            "prefer_small_pr": True,
            "run_tests": False,
        },
    }

    prompt = (
        "You are a coding agent working in the ChatUI repo.\n"
        "Your task: implement the provided GitHub issue in the local working tree.\n\n"
        "Hard rules:\n"
        "- Do NOT commit.\n"
        "- Do NOT push.\n"
        "- Return JSON ONLY.\n\n"
        "Suggested workflow:\n"
        "- Read relevant files.\n"
        "- Implement the change.\n"
        "- Update/add tests if needed.\n"
        "- Keep changes minimal.\n\n"
        "Return JSON like: {\"ok\":true,\"summary\":\"...\",\"notes\":\"...\"}\n\n"
        "INPUT_JSON:\n"
        + json.dumps(payload, ensure_ascii=False)
    )

    run = _run(
        [
            "openclaw",
            "agent",
            "--agent",
            PM_AGENT_ID,
            "--thinking",
            "medium",
            "--json",
            "--timeout",
            "1800",
            "--message",
            prompt,
        ],
        cwd=REPO_ROOT,
    )

    outer = json.loads(run.stdout or "{}")
    return _parse_json_payload_from_openclaw(outer)


def write_daily_plan(items: list[dict], proposals: list[dict], created_issue_urls: list[str]) -> Path:
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
            meta = it.get("metadata") or {}
            tag = f" type={meta.get('type')}" if meta.get("type") else ""
            lines.append(f"- freeform {it['id']}{tag}: {t[:160]}")

    lines.append("")
    lines.append("## OpenClaw proposals")
    if proposals:
        for p in proposals:
            lines.append(f"- action={p.get('action')} title={p.get('title')!r} duplicate_of={p.get('duplicate_of')!r}")
    else:
        lines.append("- (none)")

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


# -------- Mode entrypoints --------

def triage_main() -> int:
    init_db()

    started_at = now_iso()
    since = latest_run_finished_at()
    items = fetch_new_feedback(since)

    if not items:
        record_run(started_at, now_iso(), "skipped", 0, "No new feedback")
        return 0

    existing = fetch_recent_github_issues(limit=200)

    analysis = openclaw_analyze(items, existing)
    proposals = (analysis.get("proposals") or []) if isinstance(analysis, dict) else []

    created_urls: list[str] = []
    created_n = 0
    skipped_dup = 0

    for p in proposals:
        if not isinstance(p, dict):
            continue
        action = str(p.get("action") or "").strip()
        if action == "skip_duplicate":
            skipped_dup += 1
            continue
        if action != "create":
            continue

        title = str(p.get("title") or "").strip()
        body = str(p.get("body") or "").strip()
        labels = p.get("labels")
        if isinstance(labels, list):
            labels = [str(x) for x in labels if str(x).strip()]
        else:
            labels = None

        if not title or not body:
            continue

        url = gh_issue_create(title=title, body=body, labels=labels)
        created_urls.append(url)
        created_n += 1

    plan_path = write_daily_plan(items, proposals, created_urls)

    insert_changelog_entry(
        title="PM loop: feedback triage",
        body_md=(
            f"Generated plan: `{plan_path.relative_to(REPO_ROOT)}`\n\n"
            + ("Created issues:\n" + "\n".join(f"- {u}" for u in created_urls) if created_urls else "Created issues: (none)")
        ),
    )

    record_run(
        started_at,
        now_iso(),
        "ok",
        len(items),
        f"proposals={len(proposals)} created={created_n} skipped_duplicate={skipped_dup} plan={plan_path}",
    )
    return 0


def apply_main(issue_ref: str, *, test_cmd: str = PM_TEST_CMD, relaunch_cmd: str | None = PM_RELAUNCH_CMD) -> int:
    # Preflight: require clean working tree
    status = _run(["git", "status", "--porcelain"], cwd=REPO_ROOT).stdout.strip()
    if status:
        raise SystemExit("Refusing to apply: git working tree is not clean")

    issue = gh_issue_view(issue_ref)
    if not issue or not issue.get("number"):
        raise SystemExit(f"Could not resolve issue: {issue_ref}")

    apply_result = openclaw_apply_issue(issue)
    if not isinstance(apply_result, dict) or not apply_result.get("ok"):
        raise SystemExit(f"OpenClaw apply failed or returned ok=false: {apply_result}")

    # Require that something changed
    changed = _run(["git", "status", "--porcelain"], cwd=REPO_ROOT).stdout.strip()
    if not changed:
        raise SystemExit("Apply completed but no files changed; refusing to commit")

    # Run tests
    if test_cmd.strip():
        _run_shell(test_cmd, cwd=REPO_ROOT)

    # Commit
    n = int(issue["number"])
    title = str(issue.get("title") or "").strip()[:120]
    msg = f"Apply #{n}: {title}" if title else f"Apply #{n}"

    _run(["git", "add", "-A"], cwd=REPO_ROOT)
    _run(["git", "commit", "-m", msg], cwd=REPO_ROOT)

    # Push
    _run(["git", "push", "origin", "HEAD"], cwd=REPO_ROOT)

    # Optional relaunch
    if relaunch_cmd and relaunch_cmd.strip():
        _run_shell(relaunch_cmd, cwd=REPO_ROOT)

    return 0


def main() -> int:
    """Backward compatible entrypoint used by existing scripts/tests (triage mode)."""
    return triage_main()


def cli_main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["triage", "apply"], default="triage")
    p.add_argument("--issue", help="Issue number or URL (apply mode)")
    p.add_argument("--test-cmd", default=PM_TEST_CMD, help='Shell command to run tests (apply mode). Default: env PM_TEST_CMD or "npm test"')
    p.add_argument("--relaunch-cmd", default=PM_RELAUNCH_CMD, help="Optional shell command to relaunch services after push (apply mode).")

    args = p.parse_args(argv)

    if args.mode == "triage":
        return triage_main()

    if not args.issue:
        raise SystemExit("--issue is required in apply mode")

    return apply_main(args.issue, test_cmd=args.test_cmd, relaunch_cmd=args.relaunch_cmd)


if __name__ == "__main__":
    raise SystemExit(cli_main())
