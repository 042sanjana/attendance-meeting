 
import os
from pathlib import Path
 
BACKEND_DIR = Path(__file__).resolve().parents[2]
 
# Root directory containing the combined project folders
PROJECT_ROOT = BACKEND_DIR.parents[2]
 
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)
 
OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "gemma3-local:latest"
)
 
OLLAMA_TIMEOUT = int(
    os.getenv("OLLAMA_TIMEOUT", "180")
)
 
OLLAMA_NUM_CTX = int(
    os.getenv("OLLAMA_NUM_CTX", "4096")
)
 
# Attendance database
ATTENDANCE_DB = os.getenv("ATTENDANCE_DB")
 
if not ATTENDANCE_DB:
    from app.database import DB_PATH
    ATTENDANCE_DB = str(DB_PATH)
 
# Organization hierarchy database
HIERARCHY_DB = os.getenv(
    "HIERARCHY_DB",
    str(BACKEND_DIR / "organization_hierarchy.db")
)
 
# Meeting database: search the combined project folders
MEETING_DB = os.getenv("MEETING_DB_PATH")
 
if not MEETING_DB:
    candidates = list(
        PROJECT_ROOT.rglob("meeting.db")
    )
 
    # Prefer the database containing both meetings and tasks.
    selected = None
 
    for candidate in candidates:
        try:
            import sqlite3
 
            connection = sqlite3.connect(
                f"file:{candidate.as_posix()}?mode=ro",
                uri=True,
            )
 
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table'"
                ).fetchall()
            }
 
            connection.close()
 
            if "meetings" in tables and "tasks" in tables:
                selected = candidate
                break
 
        except Exception:
            continue
 
    if selected is None:
        raise FileNotFoundError(
            "Meeting database with meetings and tasks "
            "tables was not found. Set MEETING_DB_PATH."
        )
 
    MEETING_DB = str(selected)
 
# ODC data is stored in the attendance database
ODC_DB = ATTENDANCE_DB
 
RAG_DIR = (
    Path(__file__).resolve().parent
    / "rag"
    / "chroma_db"
)
 
EMBEDDING_MODEL = os.getenv(
    "CHATBOT_EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2"
)
 