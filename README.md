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
- A minimal backend (TBD) to store:
  - feedback items
  - decisions / specs
  - agent runs + artifacts
- Agent integration (TBD):
  - OpenClaw orchestration (primary)
  - Claude Code / Codex as coding harness

## Architecture sketch

- **Frontend:** Vite + React + Tailwind (current)
- **Backend:** TBD (could start as a JSON store / SQLite)
- **Agent runner:** OpenClaw (orchestrator) + coding agent sessions
- **CI/CD:** TBD (GitHub Actions)

## Dev

Install deps:

```bash
npm install --legacy-peer-deps
```

Run dev server:

```bash
npm run dev
```

## Notes

- The existing codebase may contain leftover UI/components from the original project. We’ll replace/reshape incrementally.
- This README is intentionally high-level; we’ll firm up the spec once the first in-app feedback flow exists.
