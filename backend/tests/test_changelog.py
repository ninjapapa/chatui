import importlib
import os
import tempfile
import unittest

from fastapi.testclient import TestClient


class TestChangelog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        os.environ["CHATUI_DB_PATH"] = os.path.join(cls._tmp.name, "test.sqlite3")

        import app as app_module  # noqa: E402

        importlib.reload(app_module)
        cls._app_module = app_module
        cls.client = TestClient(app_module.app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        cls._tmp.cleanup()

    def test_changelog_empty(self):
        r = self.client.get("/api/changelog?limit=5")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])

    def test_changelog_ordering(self):
        # Insert two changelog entries with different created_at ordering.
        import db

        with db.get_conn() as conn:
            conn.execute(
                "INSERT INTO changelog_entries(id, title, body_md, created_at) VALUES (?, ?, ?, ?)",
                ("c1", "first", "body1", "2026-01-01T00:00:00+00:00"),
            )
            conn.execute(
                "INSERT INTO changelog_entries(id, title, body_md, created_at) VALUES (?, ?, ?, ?)",
                ("c2", "second", "body2", "2026-02-01T00:00:00+00:00"),
            )

        r = self.client.get("/api/changelog?limit=10")
        self.assertEqual(r.status_code, 200)
        items = r.json()
        self.assertEqual(items[0]["id"], "c2")
        self.assertEqual(items[1]["id"], "c1")


if __name__ == "__main__":
    unittest.main()
