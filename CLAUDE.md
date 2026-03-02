# CLAUDE.md — Project Knowledge (chatui)

This file is the "project brain" for agentic coding sessions (Claude Code/OpenClaw/etc.).

## Repo purpose

This repo is being repurposed into a **Develop-by-Using** prototype:
- users interact with the product
- users give feedback/feature asks inside the product
- agents triage → plan → implement → validate → deploy on a daily/nightly cadence

See:
- `docs/NORTHSTAR.md` (vision, constraints, phases)
- `docs/MVP_PROJECT_PLAN.md` (execution plan)

## Current MVP decisions

- **MVP storage:** SQLite
  - Decision recorded in `docs/DECISIONS.md`

## Backend (current state)

Folder: `backend/`

- Framework: **FastAPI**
- Run locally:
  ```bash
  cd backend
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  uvicorn app:app --reload --port 8080
  ```

### SQLite

- DB path default: `backend/data/chatui.sqlite3`
- Override via env var:
  ```bash
  export CHATUI_DB_PATH=/path/to/chatui.sqlite3
  ```
- Tables are created on backend startup (`init_db()` in `backend/db.py`).

### Implemented endpoints (so far)

- `GET /api/health` → `{ ok: true }`
- `GET /api/db` → `{ db_path: ... }`
- `POST /api/chat` → ensure chat exists
- `POST /api/message` → insert a message
- `GET /api/messages?chat_id=...&limit=...` → list messages
- `POST /api/feedback/answer` → thumbs up/down + optional comment tied to a message
- `POST /api/feedback/freeform` → free-form feedback

### Tests

- Tests live in `backend/tests/`
- Run:
  ```bash
  cd backend
  source .venv/bin/activate
  python -m unittest -v tests.test_connectivity
  ```

Test notes:
- `tests/test_connectivity.py` sets `CHATUI_DB_PATH` to a temp file.
- It uses `TestClient` as a context manager to ensure FastAPI startup events run (DB init).

## Frontend (current state)

- Vite + React + Tailwind
- Dev server:
  ```bash
  npm install --legacy-peer-deps
  npm run dev
  ```

## Near-term roadmap

First 3 GitHub Issues:
1. SQLite storage (this branch)
2. FastAPI serve built UI (`dist/`) + health endpoint
3. WebSocket chat plumbing (echo stub)

## Conventions / guardrails (from North Star)

- Single user MVP
- Local deploy MVP
- Always cite sources in answers (when LLM is added)
- Every answer gathers feedback (👍/👎 + optional comment)
- Nightly run happens only if there is new feedback
- Start with HITL (approve plan, approve PR, approve deploy) then reduce over time

## Project learnings (keep here, not in workspace MEMORY.md)

- Backend module imports:
  - We run uvicorn as `uvicorn app:app` from `backend/`, so `backend/app.py` must use **absolute imports** like `from db import ...` (not relative `from .db import ...`) unless we restructure it as a proper Python package.

- FastAPI startup + tests:
  - DB tables are created in a startup event; when testing with `TestClient`, use it as a **context manager** (or explicitly enter/exit) so startup events run.

- FastAPI TestClient dependencies:
  - `fastapi.testclient` requires **httpx**. Keep `httpx` pinned in `backend/requirements.txt`.

- Ports:
  - `8080` may already be in use; prefer picking a free port or ensure old uvicorn sessions are stopped.

- Shell quoting:
  - When creating GitHub issues via CLI, avoid unescaped backticks in bodies (they can be executed by the shell). Prefer `$'...'` quoting or `--body-file`.

## Regression test (run before PR)

Run the repo regression checks with:

```bash
./scripts/regression.sh
```

It performs:
- `npm run build` (frontend typecheck + production build)
- backend unit tests (requires `backend/.venv` to exist)

If `backend/.venv` is missing:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
