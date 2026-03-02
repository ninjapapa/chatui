# MVP Project Plan — Develop-by-Using Healthcare Chat (Local)

This document turns `docs/NORTHSTAR.md` into an executable MVP plan.

MVP principles:
- **Single user** (you)
- **Local deploy**
- **Always cite sources** in answers
- **Close the loop**: every answer gathers feedback (👍/👎 + optional comment)
- Nightly run happens **only if new feedback exists**

---

## 0) Current starting point

### Frontend (existing)
- This repo already has a Vite + React + Tailwind UI and an existing chat UI baseline.

### Backend reference (from old project)
The previous README shows an example backend pattern:
- **FastAPI** serving the built static files (`dist/`) and assets (`dist/assets`)
- A **WebSocket** endpoint (`/ws`) for realtime chat messages

Example snippet (from `docs/old_readme.md`):
- `app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")`
- `@app.get("/") -> FileResponse("dist/index.html")`
- `@app.websocket("/ws")` to accept client messages, run an agent, send assistant messages

We will reuse this pattern but swap in:
- our healthcare system assistant behavior
- citations requirement
- feedback capture endpoints/storage

---

## 1) MVP scope (what we will build)

### 1.1 User-facing flows
1. **Ask a question in chat** → get an answer with **citations**.
2. After each answer: provide feedback:
   - 👍 / 👎
   - optional comment
3. Submit **free-form feedback** (catch-all) from the UI.
4. View:
   - **Changelog** (what changed last run)
   - **Backlog status** (GitHub Issues links are fine for MVP)

### 1.2 System flows
1. Store:
   - chat transcript
   - per-answer rating (👍/👎)
   - optional per-answer comment
   - free-form feedback
2. A nightly (or on-demand) “PM agent” run that:
   - checks if new feedback exists
   - summarizes + clusters
   - proposes a plan
   - creates/updates GitHub Issues
   - optionally drafts PRs (later step)

---

## 2) Architecture (MVP)

### 2.1 Frontend
- Vite + React
- Chat UI
- Feedback widgets (rating + comment)
- Simple pages: Changelog, Backlog

### 2.2 Backend (MVP)
- FastAPI
- WebSocket for chat (`/ws`)
- REST endpoints for feedback:
  - `POST /api/feedback/answer` (thumb + comment, with message id)
  - `POST /api/feedback/freeform`
  - `GET /api/changelog`
  - `GET /api/health` (optional)
- Storage (MVP): SQLite or JSONL files (start simple, upgrade later)

### 2.3 LLM + citations
- Use OpenAI APIs.
- Phase 1 retrieval strategy:
  - web search + citations (implementation detail TBD)
  - optionally cache fetched pages/snippets locally to reduce cost and improve repeatability

### 2.4 QA/validation gates (MVP)
- Unit tests (backend + key UI utilities)
- UI smoke via automated tool/computer-use flow (minimum: load app, send a question, receive an answer, submit 👍)
- Rollback option:
  - for local MVP, “rollback” can be: keep last N builds and allow switching (or a script to revert to previous build)

---

## 3) Phases & milestones

### Phase 0 — Repo baseline (0.5 day)
- [ ] Confirm UI runs locally (`npm install --legacy-peer-deps`, `npm run dev`)
- [ ] Document local run commands in README (already mostly done)

**Exit criteria:** UI starts reliably.

### Phase 1 — Local backend skeleton + static hosting (1 day)
- [ ] Add a `backend/` folder with a minimal FastAPI app
- [ ] Serve built UI from FastAPI (dist + assets) following `docs/old_readme.md`
- [ ] Add `/ws` websocket echo stub (no LLM yet)

**Exit criteria:** `backend` can serve the UI build; websocket connects.

### Phase 2 — Chat roundtrip with LLM + citations (2–4 days)
- [ ] Implement `/ws` chat handling that calls the LLM
- [ ] Enforce response format:
  - answer in Markdown
  - citations included (links or footnotes)
- [ ] Persist transcript

**Exit criteria:** ask a healthcare question → get cited answer; transcript saved.

### Phase 3 — Feedback capture (1–2 days)
- [ ] Add per-answer rating UI (👍/👎) + optional comment
- [ ] Implement feedback endpoints + storage
- [ ] Add free-form feedback box + storage

**Exit criteria:** every answer produces a feedback event stored in backend.

### Phase 4 — Changelog + backlog integration (2–3 days)
- [ ] Add changelog page (reads from backend)
- [ ] Add backlog page (links to GitHub Issues, or fetch list via GitHub API later)
- [ ] Define a simple changelog schema (date, items shipped, links)

**Exit criteria:** user can see what changed and what’s planned.

### Phase 5 — “PM agent” nightly loop (3–6 days)
- [ ] Implement a script/job that:
  - checks “new feedback since last run”
  - produces a daily plan
  - writes plan summary to `docs/` or backend storage
  - creates/updates GitHub Issues
- [ ] Add a manual trigger in UI or CLI to run it now

**Exit criteria:** feedback collected → next day there is a plan + backlog updates.

### Phase 6 — QA automation + rollback (2–5 days)
- [ ] Add unit tests + CI skeleton (local first, GitHub Actions later)
- [ ] Add UI smoke test automation
- [ ] Implement local rollback mechanism

**Exit criteria:** nightly loop is safer and repeatable.

---

## 4) Work breakdown (first 7 tasks)

1. **Decide storage** for MVP (SQLite vs JSONL)
2. Create `backend/` FastAPI skeleton
3. Build + serve frontend from FastAPI (`dist/`)
4. WebSocket chat plumbing (client ↔ server)
5. Add LLM call + enforce citations format
6. Add feedback UI + endpoints
7. Add changelog page + backend endpoint

---

## 5) Key decisions to confirm (blocking)

1. **Citations format:**
   - Inline links vs numbered footnotes? (Recommend: numbered footnotes for consistency)
2. **Search strategy:**
   - Use an external search API vs curated sources vs fetch-and-summarize?
3. **Storage choice:**
   - Start with SQLite (cleaner) or JSONL (simpler)?
4. **Nightly schedule:**
   - What time to run? (local cron) + what counts as “new feedback”?

---

## 6) Definition of Done (MVP)

MVP is “done” when:
- You can ask healthcare system questions and get cited answers.
- Every answer collects feedback (👍/👎 + optional comment).
- Feedback persists and is usable by the nightly PM-agent loop.
- The system can skip nightly runs when there is no new feedback.
- You can see a changelog and backlog status.
