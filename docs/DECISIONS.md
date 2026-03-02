# Project decisions

## MVP storage: SQLite

**Decision:** Use SQLite for MVP storage.

**Why:**
- Small, local, zero-ops
- Easy to query and evolve beyond JSONL
- Supports stable schemas for chat/feedback artifacts

**Initial entities:**
- chats
- messages
- answer_feedback
- freeform_feedback

**Implementation:** `backend/db.py` creates tables automatically on backend startup.
