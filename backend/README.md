# Backend (MVP)

Local FastAPI backend for the ChatUI MVP.

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run
uvicorn backend.app:app --reload --port 8080
```

## Storage

SQLite database path:
- defaults to `./data/chatui.sqlite3`
- override with `CHATUI_DB_PATH=/path/to/file.sqlite3`

Tables are created automatically on startup.
