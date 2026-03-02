import os
import sqlite3
import tempfile
import unittest
from pathlib import Path


class TestDbInit(unittest.TestCase):
    def test_init_db_creates_tables(self):
        tmp = tempfile.TemporaryDirectory()
        try:
            db_path = Path(tmp.name) / "t.sqlite3"
            os.environ["CHATUI_DB_PATH"] = str(db_path)

            # Import after env var set
            import importlib
            import db as db_module  # noqa: E402

            importlib.reload(db_module)
            db_module.init_db(db_module.DEFAULT_DB_PATH)

            conn = sqlite3.connect(str(db_path))
            try:
                rows = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ).fetchall()
                tables = {r[0] for r in rows}

                expected = {
                    "chats",
                    "messages",
                    "answer_feedback",
                    "freeform_feedback",
                    "changelog_entries",
                    "pm_runs",
                }
                self.assertTrue(expected.issubset(tables))
            finally:
                conn.close()
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
