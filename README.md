# ChatUI — Develop-by-Using Prototype

ChatUI is a prototype for a “develop-by-using” product loop:
- users submit feedback in-context
- an agent triages/dedupes it into GitHub issues
- the agent can optionally implement an issue and ship an update

## Quick start (local dev)

### 1) Install deps

```bash
npm ci

cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

### 2) Run dev servers

Backend (FastAPI):

```bash
cd backend
source .venv/bin/activate
uvicorn app:app --reload --host 127.0.0.1 --port 8080
```

Frontend (Vite):

```bash
npm run dev
```

Open the Vite URL (usually `http://127.0.0.1:5173` or `:5174`).

### 3) Run tests

```bash
npm test
```

## PM loop (triage + optional apply)

One-command (default: triage + apply first created issue):

```bash
./scripts/pm_loop_run.sh
```

Triage only:

```bash
PM_LOOP_APPLY=0 ./scripts/pm_loop_run.sh
```

## Docs

More detailed docs live in `docs/`:

- PM agent setup: `docs/OPENCLAW_PM_AGENT.md`
- Decisions: `docs/DECISIONS.md`
- Northstar: `docs/NORTHSTAR.md`
- MVP plan: `docs/MVP_PROJECT_PLAN.md`
- UI notes: `docs/UI_stack.md`

## Architecture

- Frontend: Vite + React + Tailwind
- Backend: FastAPI
- Storage: SQLite
