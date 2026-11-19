import os
from pathlib import Path

# backend/app/chatbot/config.py
BACKEND_DIR = Path(__file__).resolve().parents[2]

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "gemma3-local:latest"
)

# Keep requests bounded to reduce local model timeouts.
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "180"))
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "4096"))

# Existing application databases. Do not create replacement databases.
ATTENDANCE_DB = os.getenv("ATTENDANCE_DB")

if not ATTENDANCE_DB:
    try:
        from app.database import DB_PATH
        ATTENDANCE_DB = str(DB_PATH)
    except Exception as exc:
        raise RuntimeError(
            "Could not obtain DB_PATH from app.database. "
            "Check your existing database.py."
        ) from exc

HIERARCHY_DB = os.getenv(
    "HIERARCHY_DB",
    str(BACKEND_DIR / "organization_hierarchy.db")
)

MEETING_DB = os.getenv("MEETING_DB_PATH")

if not MEETING_DB:
   

    meeting_candidates = list(BACKEND_DIR.rglob("meeting.db"))
    
   

    MEETING_DB = (
        str(_meeting_candidates[0])
        if _meeting_candidates
        else str(BACKEND_DIR / "meeting.db")
    )

# ODC models in your supplied router use the application's
# database module, so ODC is read from the same DB file.
ODC_DB = ATTENDANCE_DB

RAG_DIR = Path(__file__).resolve().parent / "rag" / "chroma_db"
EMBEDDING_MODEL = os.getenv(
    "CHATBOT_EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2"
)
