import importlib
import os
import tempfile
import unittest
from pathlib import Path


class TestPmLoop(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.sqlite3")
        os.environ["CHATUI_DB_PATH"] = self.db_path

        # Import modules after env var is set.
        import db as db_module

        importlib.reload(db_module)
        db_module.init_db(db_module.DEFAULT_DB_PATH)

        import pm_loop as pm

        # also import gh loop module
        import pm_loop_gh as pmgh

        importlib.reload(pmgh)
        self.pmgh = pmgh

        importlib.reload(pm)
        self.pm = pm

        # Redirect docs/daily output to temp.
        self.repo_root = Path(self._tmp.name) / "repo"
        self.repo_root.mkdir(parents=True, exist_ok=True)
        (self.repo_root / "docs").mkdir(exist_ok=True)

        self.pm.REPO_ROOT = self.repo_root
        self.pm.DAILY_DIR = self.repo_root / "docs" / "daily"

        self.pmgh.REPO_ROOT = self.repo_root
        self.pmgh.DAILY_DIR = self.repo_root / "docs" / "daily"
        self.pmgh.GITHUB_REPO = "owner/repo"

    def tearDown(self):
        self._tmp.cleanup()

    def test_skips_when_no_new_feedback(self):
        rc = self.pm.main()
        self.assertEqual(rc, 0)
        self.assertFalse(self.pm.DAILY_DIR.exists())

        import db

        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT status, new_feedback_count FROM pm_runs ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
            self.assertEqual(row[0], "skipped")
            self.assertEqual(row[1], 0)

    def test_writes_plan_and_changelog_when_feedback_exists(self):
        import db

        # Insert one freeform feedback to trigger the run.
        with db.get_conn() as conn:
            conn.execute(
                "INSERT INTO freeform_feedback(id, chat_id, text, created_at, metadata_json) VALUES (?, ?, ?, ?, ?) ",
                ("ff1", "chat1", "hello", "2026-03-02T00:00:00+00:00", None),
            )

        rc = self.pm.main()
        self.assertEqual(rc, 0)

        # Plan file exists
        self.assertTrue(self.pm.DAILY_DIR.exists())
        plans = list(self.pm.DAILY_DIR.glob("*-plan.md"))
        self.assertEqual(len(plans), 1)
        content = plans[0].read_text()
        self.assertIn("New feedback items", content)

        # Changelog entry inserted
        with db.get_conn() as conn:
            chg = conn.execute(
                "SELECT id, title FROM changelog_entries ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            self.assertIsNotNone(chg)

            run = conn.execute(
                "SELECT status, new_feedback_count FROM pm_runs ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
            self.assertEqual(run[0], "ok")
            self.assertGreaterEqual(run[1], 1)


if __name__ == "__main__":
    unittest.main()

class TestPmLoopGh(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.sqlite3")
        os.environ["CHATUI_DB_PATH"] = self.db_path

        import db as db_module

        importlib.reload(db_module)
        db_module.init_db(db_module.DEFAULT_DB_PATH)

        import pm_loop_gh as pmgh

        importlib.reload(pmgh)
        self.pmgh = pmgh

        # Redirect docs output to temp
        self.repo_root = Path(self._tmp.name) / "repo"
        self.repo_root.mkdir(parents=True, exist_ok=True)
        (self.repo_root / "docs").mkdir(exist_ok=True)
        self.pmgh.REPO_ROOT = self.repo_root
        self.pmgh.DAILY_DIR = self.repo_root / "docs" / "daily"

        # Monkeypatch gh issue creation to avoid network
        self.created = []

        def _fake_create(title: str, body: str, labels=None):
            url = f"https://example.com/{title.replace(' ', '_')}"
            self.created.append(url)
            return url

        self.pmgh.gh_issue_create = _fake_create

    def tearDown(self):
        self._tmp.cleanup()

    def test_creates_issue_for_feature_request(self):
        import db

        with db.get_conn() as conn:
            conn.execute(
                "INSERT INTO freeform_feedback(id, chat_id, text, created_at, metadata_json) VALUES (?, ?, ?, ?, ?)",
                (
                    "ff1",
                    "chat1",
                    "Feature request: X",
                    "2026-03-02T00:00:00+00:00",
                    '{"type":"feature_request","title":"Add X"}',
                ),
            )

        rc = self.pmgh.main()
        self.assertEqual(rc, 0)
        self.assertEqual(len(self.created), 1)

        # Plan written
        plans = list((self.pmgh.DAILY_DIR).glob("*-plan.md"))
        self.assertEqual(len(plans), 1)

