# ChatUI → "Develop-by-Using" Prototype

This repo is being repurposed.

The new goal: **prototype a “develop-by-using” product loop** where real users can:

- Use the product
- Submit feedback + feature requests in-context
- Have an agent (OpenClaw and/or Claude Code) translate that feedback into:
  - clarified requirements
  - an actionable plan
  - code changes
  - a deployed update

…and repeat this **daily**.

## What this is (concept)

**Develop-by-Using** = shorten the distance between:

1. *User intent* (feedback / feature asks)
2. *Implementation* (agent-assisted coding)
3. *Delivery* (automatic deploy)

The system should behave like a product that evolves continuously based on actual usage.

## Intended workflow (daily loop)

1. **Collect feedback**
   - In-app feedback UI (notes, bugs, feature requests)
   - Optional: attach context (page, screenshot, logs)

2. **Triage + clarify**
   - Agent summarizes, dedupes, and asks follow-up questions
   - Produces a short “spec” for each accepted item

3. **Implement**
   - Agent opens/updates tasks
   - Applies code changes
   - Runs tests / lint

4. **Deploy**
   - Build + ship to a preview/prod environment
   - Post a changelog back into the app

5. **Measure + repeat**
   - Track what shipped, what didn’t, and why

## MVP scope (initial)

- A simple app UI (this repo) with:
  - auth-free feedback capture (for prototyping)
  - a “feature requests” list + status
  - a changelog view
- A minimal backend to store:
  - feedback items
  - decisions / specs
  - agent runs + artifacts
- Agent integration (TBD):
  - OpenClaw orchestration (primary)
  - Claude Code / Codex as coding harness

## Architecture sketch

- **Frontend:** Vite + React + Tailwind
- **Backend:** FastAPI (local MVP)
- **Storage:** SQLite (see `docs/DECISIONS.md`)

## Local dev

### 1) Frontend dev server

Install deps:

```bash
npm install --legacy-peer-deps
```

Run dev server:

```bash
npm run dev
```

### 2) Backend (FastAPI)

Create a Python venv and install deps:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the backend:

```bash
uvicorn backend.app:app --reload --port 8080
```

### 3) Build + serve the frontend via backend

Build the frontend:

```bash
cd ..
npm run build
```

Then run the backend (it serves `dist/`):

```bash
cd backend
source .venv/bin/activate
FRONTEND_DIST="../dist" uvicorn backend.app:app --reload --port 8080
```

## Nightly PM loop

To run the PM loop on-demand (creates/updates GitHub issues from new feedback; skips if none):

```bash
./scripts/pm_loop_run.sh
```

To install a nightly cron (default 02:10 local time):

```bash
./scripts/install_pm_cron.sh
# optional: pass a custom cron schedule, e.g.
./scripts/install_pm_cron.sh "0 1 * * *"
```

To uninstall:

```bash
./scripts/uninstall_pm_cron.sh
```

Logs:
- `backend/data/pm_loop.log`

## Tests

### One-command (recommended)

```bash
npm test
```

This runs:
- frontend build + lint
- backend unit tests (requires `backend/.venv`)
- Playwright smoke test (installs Chromium on first run)

### Individual commands

```bash
npm run lint
npm run backend:test
npm run smoke
npm run regression
```

## Notes

- The existing codebase may contain leftover UI/components from the original project. We’ll replace/reshape incrementally.
