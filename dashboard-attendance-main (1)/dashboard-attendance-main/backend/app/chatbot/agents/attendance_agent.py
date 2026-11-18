

from app.chatbot.tools.attendance_tools import query_odc
from app.chatbot.tools.schema_discovery import get_module_schema


def run_odc_agent(question: str) -> dict:
    schema = get_module_schema("odc")

    prompt = f"""
You are an SQLite query planner for an ODC tracker database.

SCHEMA:
{schema}

QUESTION:
{question}

RULES:
- Return one SQLite SELECT query only.
- Use only the displayed tables and columns.
- odc_employees contains the ODC employee roster.
- odc_logs contains date-level ODC records.
- Count distinct log_date values for employee working days.
- Do not count multiple LOB/DM rows on the same employee date as
  multiple working days.
- Never modify the database.
- Return SQL only.
"""

    response = get_llm().invoke(prompt)
    sql = extract_sql(response.content)

    return {
        "module": "odc",
        "sql": sql,
        "data": query_odc(sql),
    }
import re

from langchain_ollama import ChatOllama

from app.chatbot.config import (
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_TIMEOUT,
    OLLAMA_NUM_CTX,
)
from app.chatbot.tools.attendance_tools import (
    get_attendance_schema,
    query_attendance,
)

def get_llm():
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
        num_ctx=OLLAMA_NUM_CTX,
        client_kwargs={
            "timeout": OLLAMA_TIMEOUT
        },
    )



def extract_sql(text: str) -> str:
    match = re.search(
        r"```sql\s*(.*?)```",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:
        return match.group(1).strip()

    match = re.search(
        r"(SELECT\b.*)",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    if not match:
        raise ValueError("Gemma did not return a SELECT query.")

    return match.group(1).strip()


def run_attendance_agent(question: str) -> dict:
    schema = get_attendance_schema()

    prompt = f"""
You are an SQLite query planner for an HR attendance database.

DATABASE SCHEMA:
{schema}

USER QUESTION:
{question}

RULES:
- Return exactly one SQLite SELECT query.
- Use only tables and columns shown in the schema.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER or PRAGMA.
- Do not invent columns.
- For attendance counts, use SQL COUNT and GROUP BY.
- For percentages, calculate from actual database counts.
- Use the attendance date column shown in the schema.
- Limit detailed employee lists to 100 rows.
- Return SQL only, preferably inside a sql code block.
"""

    llm = get_llm()
    response = llm.invoke(prompt)
    sql = extract_sql(response.content)

    result = query_attendance(sql)

    return {
        "module": "attendance",
        "sql": sql,
        "data": result,
    }
