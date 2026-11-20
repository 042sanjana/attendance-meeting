 
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
    query_odc,
)
 
from app.chatbot.tools.schema_discovery import get_module_schema
 
 
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
 
 
def extract_sql(response_text: str) -> str:
    """Extract a single SELECT statement from the model response."""
 
    match = re.search(
        r"```sql\s*(.*?)```",
        response_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
 
    if match:
        sql = match.group(1).strip()
    else:
        match = re.search(
            r"\bSELECT\b.*",
            response_text,
            flags=re.IGNORECASE | re.DOTALL,
        )
 
        if not match:
            raise ValueError(
                "The model did not return a SELECT query."
            )
 
        sql = match.group(0).strip()
 
    sql = sql.rstrip(";").strip()
 
    if not re.match(r"^SELECT\b", sql, re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")
 
    if ";" in sql:
        raise ValueError("Multiple SQL statements are not allowed.")
 
    forbidden = re.search(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|"
        r"ATTACH|DETACH|PRAGMA)\b",
        sql,
        re.IGNORECASE,
    )
 
    if forbidden:
        raise ValueError("Unsafe SQL operation detected.")
 
    return sql
 
 
def find_employee_id(question: str):
    """Extract an employee ID from natural-language questions."""
 
    patterns = [
        r"\bemp(?:loyee)?\s*id\s*[:#]?\s*([A-Za-z0-9_-]+)",
        r"\bemp\s*[:#]\s*([A-Za-z0-9_-]+)",
    ]
 
    for pattern in patterns:
        match = re.search(
            pattern,
            question,
            re.IGNORECASE,
        )
 
        if match:
            return match.group(1).strip()
 
    return None

 
 
def run_attendance_agent(question: str) -> dict:
 
    # --------------------------------------------------
    # 1. Direct employee ID lookup.
    # Does not require Ollama.
    # --------------------------------------------------
 
    employee_id = find_employee_id(question)
 
    if employee_id:
 
        # IDs are restricted to letters, digits, _ and -.
        safe_id = employee_id.replace("'", "''")
 
        sql = f"""
            SELECT
                emp_id,
                name
            FROM employees
            WHERE CAST(emp_id AS TEXT) = '{safe_id}'
            LIMIT 1
        """
 
        result = query_attendance(sql)
 
        return {
            "module": "attendance",
            "lookup_type": "employee_by_id",
            "employee_id": employee_id,
            "data": result,
        }
 
    # --------------------------------------------------
    # 2. Normal attendance questions.
    # --------------------------------------------------
 
    schema = get_attendance_schema()
 
    prompt = f"""
You are an SQLite query planner for an HR attendance system.
 
DATABASE SCHEMA:
{schema}
 
USER QUESTION:
{question}
 
RULES:
 
1. Return exactly one SQLite SELECT query.
2. Use only tables and columns shown in the schema.
3. The employees table contains employee IDs and names.
4. The attendance table contains daily attendance records.
5. Join employees and attendance using emp_id when names are needed.
6. Use COUNT(*) for counting attendance records.
7. Use COUNT(DISTINCT emp_id) for counting unique employees.
8. Use GROUP BY for employee-wise or status-wise summaries.
9. Use the actual date column shown in the schema.
10. For daily questions without a specified date,
    use the latest available attendance date.
11. For all-time questions, do not add an arbitrary date filter.
12. Do not invent employee IDs, names, dates or columns.
13. Limit detailed employee lists to 100 rows.
14. Never use INSERT, UPDATE, DELETE, DROP or ALTER.
15. Return SQL only, preferably inside a sql code block.
 
IMPORTANT:
Do not assume the current date is the date of the records.
Use dates stored in the database.
"""
 
    response = get_llm().invoke(prompt)
 
    sql = extract_sql(response.content)
 
    result = query_attendance(sql)
 
    return {
        "module": "attendance",
        "sql": sql,
        "data": result,
    }
 
 
# --------------------------------------------------
# ODC AGENT
# --------------------------------------------------
 
def run_odc_agent(question: str) -> dict:
 
    schema = get_module_schema("odc")
 
    prompt = f"""
You are an SQLite query planner for an ODC tracker.
 
DATABASE SCHEMA:
{schema}
 
USER QUESTION:
{question}
 
RULES:
 
1. Return one SQLite SELECT query only.
2. Use only actual tables and columns.
3. odc_employees contains employee roster information.
4. odc_logs contains ODC working-day records.
5. A working day is a unique employee and calendar-date combination.
6. Avoid counting duplicate log rows for the same employee and date.
7. Do not invent date filters.
8. If no date is specified, use all available dates.
9. Never modify the database.
10. Return SQL only.
 
IMPORTANT:
For total employee working days, count unique combinations
of emp_id and date(log_date), not just distinct calendar dates.
"""
 
    response = get_llm().invoke(prompt)
 
    sql = extract_sql(response.content)
 
    result = query_odc(sql)
 
    return {
        "module": "odc",
        "sql": sql,
        "data": result,
    }
 