import importlib
import os
import tempfile
import unittest

from fastapi.testclient import TestClient


class TestConnectivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Make the DB path deterministic + isolated for tests.
        cls._tmp = tempfile.TemporaryDirectory()
        os.environ["CHATUI_DB_PATH"] = os.path.join(cls._tmp.name, "test.sqlite3")

        # Import after env var is set (DEFAULT_DB_PATH is computed at import time).
        import app as app_module  # noqa: E402

        importlib.reload(app_module)
        cls.client = TestClient(app_module.app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        cls._tmp.cleanup()

    def test_health(self):
        r = self.client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"ok": True})

    def test_websocket_echo(self):
        with self.client.websocket_connect("/ws") as ws:
            ws.send_text("\"hello\"")
            data = ws.receive_json()
            self.assertEqual(data["role"], "assistant")
            self.assertIn("You said", data["content"])
            self.assertIn("hello", data["content"])


    def test_db_info(self):
        r = self.client.get("/api/db")
        self.assertEqual(r.status_code, 200)
        self.assertIn("db_path", r.json())

    def test_chat_message_and_feedback_roundtrip(self):
        chat_id = "chat_test_1"

        r = self.client.post("/api/chat", json={"chat_id": chat_id})
        self.assertEqual(r.status_code, 200)

        # Create a user message
        r = self.client.post(
            "/api/message",
            json={
                "id": "m_user_1",
                "chat_id": chat_id,
                "role": "user",
                "content": "hello",
            },
        )
        self.assertEqual(r.status_code, 200)

        # Create an assistant message (the one we will rate)
        r = self.client.post(
            "/api/message",
            json={
                "id": "m_asst_1",
                "chat_id": chat_id,
                "role": "assistant",
                "content": "hi there",
                "parent_message_id": "m_user_1",
            },
        )
        self.assertEqual(r.status_code, 200)

        # Read messages
        r = self.client.get(f"/api/messages?chat_id={chat_id}&limit=50")
        self.assertEqual(r.status_code, 200)
        msgs = r.json()
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["role"], "user")
        self.assertEqual(msgs[1]["role"], "assistant")

        # Rate assistant message
        r = self.client.post(
            "/api/feedback/answer",
            json={
                "id": "fb_1",
                "chat_id": chat_id,
                "message_id": "m_asst_1",
                "thumbs": 1,
                "comment": "good",
            },
        )
        self.assertEqual(r.status_code, 200)

        # Freeform feedback
        r = self.client.post(
            "/api/feedback/freeform",
            json={
                "id": "ff_1",
                "chat_id": chat_id,
                "text": "please add X",
            },
        )
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()
