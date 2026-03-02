from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DB_PATH = Path(os.environ.get("CHATUI_DB_PATH", "./data/chatui.sqlite3"))


def ensure_parent_dir(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_conn(db_path: Path = DEFAULT_DB_PATH):
    ensure_parent_dir(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    with get_conn(db_path) as conn:
        cur = conn.cursor()

        # A "chat" is a session/thread of messages.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
              id TEXT PRIMARY KEY,
              created_at TEXT NOT NULL
            );
            """
        )

        # Every message in a chat (user or assistant).
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
              id TEXT PRIMARY KEY,
              chat_id TEXT NOT NULL,
              role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
              content TEXT NOT NULL,
              created_at TEXT NOT NULL,
              parent_message_id TEXT,
              metadata_json TEXT,
              FOREIGN KEY(chat_id) REFERENCES chats(id)
            );
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_chat_id_created_at ON messages(chat_id, created_at);"
        )

        # Feedback tied to an assistant message (typically the answer).
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS answer_feedback (
              id TEXT PRIMARY KEY,
              chat_id TEXT NOT NULL,
              message_id TEXT NOT NULL,
              thumbs INTEGER NOT NULL CHECK(thumbs IN (1,-1)),
              comment TEXT,
              created_at TEXT NOT NULL,
              metadata_json TEXT,
              FOREIGN KEY(chat_id) REFERENCES chats(id),
              FOREIGN KEY(message_id) REFERENCES messages(id)
            );
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_answer_feedback_chat_id_created_at ON answer_feedback(chat_id, created_at);"
        )

        # Free-form feedback not tied to a specific answer.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS freeform_feedback (
              id TEXT PRIMARY KEY,
              chat_id TEXT,
              text TEXT NOT NULL,
              created_at TEXT NOT NULL,
              metadata_json TEXT,
              FOREIGN KEY(chat_id) REFERENCES chats(id)
            );
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_freeform_feedback_created_at ON freeform_feedback(created_at);"
        )
