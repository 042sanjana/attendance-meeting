
from app.chatbot.tools.schema_discovery import get_module_schema
from app.chatbot.tools.sql_executor import execute_select


def get_meeting_schema():
    return get_module_schema("meeting")


def query_meetings(sql: str):
    return execute_select("meeting", sql)


def get_all_meeting_documents():
    schema = get_meeting_schema()

    # The original meeting module stores transcript and summary
    # in meetings, and may also store task records in tasks.
    if "TABLE meetings:" not in schema:
        return []

    result = query_meetings(
        """
        SELECT id, file_name, transcript, summary, created_at
        FROM meetings
        ORDER BY id DESC
        """
    )

    return result["rows"]
