from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from db import DEFAULT_DB_PATH, get_conn, init_db
from llm import answer_with_citations
from models import (
    AnswerFeedbackCreate,
    ChatCreate,
    FreeformFeedbackCreate,
    MessageCreate,
    MessageOut,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


app = FastAPI(title="chatui-backend", version="0.1.0")

# Local MVP: allow frontend dev server to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# If FRONTEND_DIST is set, serve the built frontend from that directory.
# By default, expect: <repo-root>/dist
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIST_DIR = REPO_ROOT / "dist"
DIST_DIR = Path(os.environ.get("FRONTEND_DIST", str(DEFAULT_DIST_DIR))).resolve()


@app.on_event("startup")
def _startup() -> None:
    init_db(DEFAULT_DB_PATH)


# Static hosting (optional)
if DIST_DIR.exists():
    assets_dir = DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/")
def read_index():
    index_path = DIST_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Frontend build not found at {index_path}. Run `npm run build` at repo root.",
        )
    return FileResponse(str(index_path))


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/db")
def db_info():
    # Small debugging endpoint for local MVP
    return {"db_path": str(Path(DEFAULT_DB_PATH).resolve())}


@app.get("/api/changelog")
def list_changelog(limit: int = 30):
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be 1..200")
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, title, body_md, created_at
            FROM changelog_entries
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


@app.post("/api/chat")
def create_chat(payload: ChatCreate):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO chats(id, created_at) VALUES (?, ?)",
            (payload.chat_id, now_iso()),
        )
    return {"ok": True, "chat_id": payload.chat_id}


@app.post("/api/message")
def create_message(payload: MessageCreate):
    with get_conn() as conn:
        # ensure chat exists
        conn.execute(
            "INSERT OR IGNORE INTO chats(id, created_at) VALUES (?, ?)",
            (payload.chat_id, now_iso()),
        )

        metadata_json = json.dumps(payload.metadata) if payload.metadata is not None else None
        conn.execute(
            """
            INSERT INTO messages(id, chat_id, role, content, created_at, parent_message_id, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.id,
                payload.chat_id,
                payload.role,
                payload.content,
                now_iso(),
                payload.parent_message_id,
                metadata_json,
            ),
        )
    return {"ok": True, "message_id": payload.id}


@app.get("/api/messages", response_model=list[MessageOut])
def list_messages(chat_id: str, limit: int = 200):
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be 1..1000")

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, chat_id, role, content, created_at, parent_message_id, metadata_json
            FROM messages
            WHERE chat_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (chat_id, limit),
        ).fetchall()

    return [dict(r) for r in rows]


@app.post("/api/feedback/answer")
def create_answer_feedback(payload: AnswerFeedbackCreate):
    with get_conn() as conn:
        # Basic integrity check: message must exist
        msg = conn.execute(
            "SELECT id FROM messages WHERE id = ?",
            (payload.message_id,),
        ).fetchone()
        if msg is None:
            raise HTTPException(status_code=404, detail="message_id not found")

        metadata_json = json.dumps(payload.metadata) if payload.metadata is not None else None
        conn.execute(
            """
            INSERT INTO answer_feedback(id, chat_id, message_id, thumbs, comment, created_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.id,
                payload.chat_id,
                payload.message_id,
                payload.thumbs,
                payload.comment,
                now_iso(),
                metadata_json,
            ),
        )

    return {"ok": True, "feedback_id": payload.id}


@app.post("/api/feedback/freeform")
def create_freeform_feedback(payload: FreeformFeedbackCreate):
    with get_conn() as conn:
        metadata_json = json.dumps(payload.metadata) if payload.metadata is not None else None
        conn.execute(
            """
            INSERT INTO freeform_feedback(id, chat_id, text, created_at, metadata_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (payload.id, payload.chat_id, payload.text, now_iso(), metadata_json),
        )

    return {"ok": True, "feedback_id": payload.id}


# --- WebSocket (Issue #3) ---


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            raw = await websocket.receive_text()

            chat_id: str | None = None
            parent_message_id: str | None = None
            user_text: str

            try:
                msg = json.loads(raw)
            except Exception:
                msg = raw

            # Frontend sends a JSON object: { chat_id, message_id, content }
            if isinstance(msg, dict):
                chat_id = msg.get("chat_id")
                parent_message_id = msg.get("message_id")
                user_text = msg.get("content") or ""
            elif isinstance(msg, str):
                user_text = msg
            else:
                user_text = str(msg)

            assistant_id = f"asst_{uuid.uuid4().hex}"
            assistant_text = "<think>Generating answer with citations...</think>\n\n" + answer_with_citations(user_text)

            payload = {
                "id": assistant_id,
                "chat_id": chat_id,
                "parent_message_id": parent_message_id,
                "role": "assistant",
                "content": assistant_text,
            }
            await websocket.send_text(json.dumps(payload))

    except WebSocketDisconnect:
        return


@app.get("/api/feedback/answer")
def list_answer_feedback(limit: int = 100):
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be 1..500")
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, chat_id, message_id, thumbs, comment, created_at, metadata_json
            FROM answer_feedback
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/feedback/freeform")
def list_freeform_feedback(limit: int = 100):
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be 1..500")
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, chat_id, text, created_at, metadata_json
            FROM freeform_feedback
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
