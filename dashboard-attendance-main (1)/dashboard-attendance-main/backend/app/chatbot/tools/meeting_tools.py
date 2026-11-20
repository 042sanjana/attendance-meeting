from app.chatbot.tools.schema_discovery import get_module_schema
from app.chatbot.tools.sql_executor import SQLExecutionError, execute_select


def get_meeting_schema():
    return get_module_schema("meeting")


def query_meetings(sql: str):
    return execute_select("meeting", sql)


def get_all_meeting_documents():
    """Every meeting row as a dict, with full (unclipped) transcript text,
    for RAG indexing. Returns [] when the meeting database is unavailable."""
    last_error = None
    for sql in (
        "SELECT * FROM meetings ORDER BY id DESC",
        "SELECT * FROM meetings",
    ):
        try:
            result = execute_select("meeting", sql, max_rows=5000, max_cell=None)
        except SQLExecutionError as exc:
            last_error = exc
            continue
        except Exception:
            return []
        columns = result["columns"]
        return [dict(zip(columns, row)) for row in result["rows"]]
    return []