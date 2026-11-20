import logging
import os
import sqlite3
from pathlib import Path

log = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[2]

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3-local:latest")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "180"))
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "4096"))

# Attendance database (also holds the ODC tables)
ATTENDANCE_DB = os.getenv("ATTENDANCE_DB")
if not ATTENDANCE_DB:
    try:
        from app.database import DB_PATH
        ATTENDANCE_DB = str(DB_PATH)
    except Exception:
        ATTENDANCE_DB = str(BACKEND_DIR / "attendance.db")

HIERARCHY_DB = os.getenv("HIERARCHY_DB", str(BACKEND_DIR / "organization_hierarchy.db"))

_SKIP_DIRS = {"node_modules", ".git", ".venv", "venv", "env", "__pycache__",
              "site-packages", "dist", "build", ".idea", ".vscode"}


def _tables_of(path: Path) -> set[str]:
    try:
        conn = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
        try:
            return {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
    except Exception:
        return set()


def _find_meeting_db() -> str:
    """Never raises: a missing meeting database must not stop the whole app."""
    try:
        root = BACKEND_DIR.parents[2]
    except IndexError:
        root = BACKEND_DIR.parent

    both = only_meetings = any_db = None
    visited = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        visited += 1
        if visited > 20000:
            break
        if "meeting.db" not in filenames:
            continue
        candidate = Path(dirpath) / "meeting.db"
        tables = _tables_of(candidate)
        if {"meetings", "tasks"} <= tables:
            both = both or candidate
        elif "meetings" in tables:
            only_meetings = only_meetings or candidate
        any_db = any_db or candidate

    chosen = both or only_meetings or any_db
    if chosen is None:
        log.warning("meeting.db not found under %s. Set MEETING_DB_PATH.", root)
        return str(BACKEND_DIR / "meeting.db")
    return str(chosen)


MEETING_DB = os.getenv("MEETING_DB_PATH") or _find_meeting_db()

# ODC data is stored in the attendance database
ODC_DB = ATTENDANCE_DB

RAG_DIR = Path(__file__).resolve().parent / "rag" / "chroma_db"
EMBEDDING_MODEL = os.getenv("CHATBOT_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")