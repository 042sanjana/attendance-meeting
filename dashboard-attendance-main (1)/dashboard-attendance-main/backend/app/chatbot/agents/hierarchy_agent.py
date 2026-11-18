
from app.chatbot.agents.attendance_agent import (
    get_llm,
    extract_sql,
)
from app.chatbot.tools.hierarchy_tools import (
    get_hierarchy_schema,
    query_hierarchy,
)


def run_hierarchy_agent(question: str) -> dict:
    schema = get_hierarchy_schema()

    prompt = f"""
You are an SQLite query planner for an organization hierarchy database.

SCHEMA:
{schema}

QUESTION:
{question}

RULES:
- Return one SQLite SELECT query only.
- Use only the displayed tables and columns.
- Employee identifier is employee_number.
- Manager relationship uses manager_id.
- Do not invent a department column if it is not present.
- Never modify the database.
- Use LIMIT 100 for employee lists.
- Return SQL only.
"""

    response = get_llm().invoke(prompt)
    sql = extract_sql(response.content)

    return {
        "module": "hierarchy",
        "sql": sql,
        "data": query_hierarchy(sql),
    }
