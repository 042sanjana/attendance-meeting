
from app.chatbot.agents.attendance_agent import (
    get_llm,
    extract_sql,
)
from app.chatbot.tools.meeting_tools import (
    get_meeting_schema,
    query_meetings,
)


def run_meeting_agent(question: str) -> dict:
    schema = get_meeting_schema()

    prompt = f"""
You are an SQLite query planner for a meeting-notes database.

SCHEMA:
{schema}

QUESTION:
{question}

RULES:
- Return one SQLite SELECT query only.
- Use only the tables and columns in the schema.
- Meeting transcripts and summaries are text.
- The meetings table may contain tasks as JSON text.
- If the tasks table exists, use its real columns.
- Do not invent columns.
- Never modify the database.
- Limit results to 50 rows.
- Return SQL only.
"""

    response = get_llm().invoke(prompt)
    sql = extract_sql(response.content)

    return {
        "module": "meeting",
        "sql": sql,
        "data": query_meetings(sql),
    }
