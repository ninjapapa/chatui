import importlib
import os
import tempfile
import unittest

from fastapi.testclient import TestClient


class TestFeedbackList(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        os.environ["CHATUI_DB_PATH"] = os.path.join(cls._tmp.name, "test.sqlite3")

        import app as app_module  # noqa: E402

        importlib.reload(app_module)
        cls.client = TestClient(app_module.app)
        cls.client.__enter__()

        # seed chat + messages + feedback
        cls.client.post("/api/chat", json={"chat_id": "chat1"})
        cls.client.post(
            "/api/message",
            json={"id": "m1", "chat_id": "chat1", "role": "assistant", "content": "a"},
        )
        cls.client.post(
            "/api/feedback/answer",
            json={
                "id": "afb1",
                "chat_id": "chat1",
                "message_id": "m1",
                "thumbs": 1,
                "comment": "good",
            },
        )
        cls.client.post(
            "/api/feedback/freeform",
            json={"id": "ff1", "chat_id": "chat1", "text": "note"},
        )

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        cls._tmp.cleanup()

    def test_list_answer_feedback(self):
        r = self.client.get("/api/feedback/answer?limit=10")
        self.assertEqual(r.status_code, 200)
        items = r.json()
        self.assertGreaterEqual(len(items), 1)
        self.assertEqual(items[0]["id"], "afb1")

    def test_list_freeform_feedback(self):
        r = self.client.get("/api/feedback/freeform?limit=10")
        self.assertEqual(r.status_code, 200)
        items = r.json()
        self.assertGreaterEqual(len(items), 1)
        self.assertEqual(items[0]["id"], "ff1")


if __name__ == "__main__":
    unittest.main()
