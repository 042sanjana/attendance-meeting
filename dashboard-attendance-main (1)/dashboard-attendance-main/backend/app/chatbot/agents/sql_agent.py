"""Shared LLM access + dynamic, schema-grounded SQL generation for every module."""
import logging
import re
from functools import lru_cache

from langchain_ollama import ChatOllama

from app.chatbot.config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_NUM_CTX,
    OLLAMA_TIMEOUT,
)
from app.chatbot.tools.schema_discovery import get_date_context, get_module_schema
from app.chatbot.tools.sql_executor import (
    DatabaseUnavailable,
    SQLExecutionError,
    UnsafeSQL,
    execute_select,
)

log = logging.getLogger(__name__)


class LLMUnavailable(Exception):
    """Ollama did not answer (not running, model missing, timeout)."""


@lru_cache(maxsize=4)
def get_llm(num_predict: int | None = None):
    kwargs = {"num_predict": num_predict} if num_predict else {}
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
        num_ctx=OLLAMA_NUM_CTX,
        client_kwargs={"timeout": OLLAMA_TIMEOUT},
        **kwargs,
    )


def call_llm(prompt: str, num_predict: int | None = None) -> str:
    try:
        response = get_llm(num_predict).invoke(prompt)
    except Exception as exc:  # connection refused, timeout, unknown model ...
        log.warning("Ollama call failed: %s", exc)
        raise LLMUnavailable(str(exc)) from exc
    return (response.content or "").strip()


_SQL_START = re.compile(
    r"\bSELECT\b|\bWITH\s+(?:RECURSIVE\s+)?\w+\s+AS\s*\(", re.I
)


def extract_sql(text: str) -> str:
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", text, re.I | re.S)
    candidate = fenced.group(1) if fenced else text
    start = _SQL_START.search(candidate)
    if not start:
        raise ValueError("The model did not return a SELECT query.")
    return candidate[start.start():].split(";")[0].strip()


DESCRIPTIONS = {
    "attendance": "an HR attendance database",
    "odc": "an ODC tracker database",
    "hierarchy": "an organization hierarchy database",
    "meeting": "a meeting-notes database",
}

COMMON_RULES = """- Output exactly one SQLite SELECT statement inside a ```sql code block and nothing else.
- Use only the tables and columns listed in the schema. Never invent columns or tables.
- Employee IDs are TEXT. Always write them as quoted strings, e.g. emp_id = '2693960'.
- For name, location or project filters use LOWER(column) LIKE LOWER('%value%').
- When counting people use COUNT(DISTINCT id_column); never count rows produced by a join.
- Compare text values such as status case-insensitively: LOWER(a.status) = 'absent'. Use the exact spelling of the values listed in the schema.
- Always wrap date columns in date(): date(a."date") = '2026-01-31'. Follow the DATE CONTEXT exactly for 'today', 'this month' and ranges.
- If the question names no date or period, use the 'today' date given in the DATE CONTEXT.
- Put LIMIT 100 on lists of rows.
- When listing employees include the ID and name columns.
- Give every selected expression a clear alias."""

MODULE_RULES = {
    "attendance": """- 'Present', 'absent', 'WFH' etc. are values of attendance.status; use the exact values listed in the schema.
- Who is present/absent on a date: SELECT e.emp_id, e.name, a.status FROM attendance a JOIN employees e ON e.emp_id = a.emp_id WHERE date(a."date") = '<date>' AND LOWER(a.status) = LOWER('<status>').
- Summary: SELECT a.status, COUNT(DISTINCT a.emp_id) AS employees, COUNT(*) AS days FROM attendance a WHERE date(a."date") BETWEEN '<start>' AND '<end>' GROUP BY a.status.
- Status values in this system: Present, Absent, WFH, Leave, Half Day, Casual/Sick leave, Earned Leave, Compensatory Leave, Public Holiday, Weekly Holiday, Optional Holiday.
- "On leave" means any status containing 'leave' (LOWER(a.status) LIKE '%leave%'); "holiday" means any status containing 'holiday'; "working" means Present, WFH or Half Day.
- Do not treat employees with no attendance row as absent unless explicitly asked.
- Percentages: ROUND(100.0 * part / total, 1) computed from real counts.""",
    "odc": """- ODC working days of an employee = COUNT(DISTINCT log_date) in odc_logs. Several LOB/DM rows on the same date count ONCE.
- Use odc_employees LEFT JOIN a grouped odc_logs subquery so employees with 0 days still appear.""",
    "hierarchy": """- Direct reports of a manager: employees whose manager_id equals the manager's employee_number. If a name is given, look the manager up by name first (join or subquery).
- Whole hierarchy: select employee_number, employee_name, designation, manager_id and the manager's name via a self LEFT JOIN, ordered by manager name then employee name.
- There is no department column; use designation / location instead.""",
    "meeting": """- Latest meeting = ORDER BY the newest date/created/id column DESC LIMIT 1.
- Pending tasks: use the real status column of the tasks table if it exists; if tasks are JSON text inside meetings, select the text so it can be read.
- Never select password or user tables.""",
}

EXAMPLES = {
    "attendance": """-- How many employees were present / absent / WFH per status on a date
SELECT a.status, COUNT(DISTINCT a.emp_id) AS employees FROM attendance a
WHERE date(a."date") = '2026-03-02' GROUP BY a.status ORDER BY employees DESC
-- Attendance days of one employee in a month
SELECT a.status, COUNT(*) AS days FROM attendance a
WHERE a.emp_id = '2693960' AND date(a."date") BETWEEN '2026-03-01' AND '2026-03-31' GROUP BY a.status""",
    "odc": """-- ODC working days per employee (roster plus anyone who has logs); one day per employee per date
SELECT ids.emp_id, COALESCE(r.name, MAX(l.emp_name)) AS name,
       COUNT(DISTINCT date(l.log_date)) AS odc_working_days
FROM (SELECT emp_id FROM odc_employees UNION SELECT emp_id FROM odc_logs) ids
LEFT JOIN odc_employees r ON r.emp_id = ids.emp_id
LEFT JOIN odc_logs l ON l.emp_id = ids.emp_id
GROUP BY ids.emp_id ORDER BY odc_working_days DESC, name LIMIT 100
-- Same for one month: put the month filter in the JOIN condition, e.g.
--   LEFT JOIN odc_logs l ON l.emp_id = ids.emp_id AND strftime('%Y-%m', l.log_date) = '2026-03'""",
    "hierarchy": """-- Direct reports of a manager given by name
SELECT e.employee_number, e.employee_name, e.designation, e.location FROM employees e
WHERE e.manager_id = (SELECT employee_number FROM employees
                      WHERE LOWER(employee_name) LIKE LOWER('%john%') LIMIT 1)
ORDER BY e.employee_name LIMIT 100
-- Managers with the number of direct reports
SELECT m.employee_number, m.employee_name, COUNT(e.employee_number) AS direct_reports
FROM employees m JOIN employees e ON e.manager_id = m.employee_number
GROUP BY m.employee_number, m.employee_name ORDER BY direct_reports DESC LIMIT 100
-- Whole hierarchy with manager names
SELECT e.employee_number, e.employee_name, e.designation, m.employee_name AS manager_name
FROM employees e LEFT JOIN employees m ON m.employee_number = e.manager_id
ORDER BY manager_name, e.employee_name LIMIT 100""",
    "meeting": """-- Pattern only: use the REAL table and column names from the schema above.
-- Latest meeting (never select the long transcript unless asked):
SELECT id, file_name, summary FROM meetings ORDER BY id DESC LIMIT 1
-- Pending tasks with their meeting (adapt the column names; compare status case-insensitively):
SELECT t.*, m.file_name FROM tasks t JOIN meetings m ON m.id = t.meeting_id
WHERE LOWER(COALESCE(t.status, 'pending')) NOT IN ('completed', 'done') LIMIT 50""",
}

ID_TEMPLATES = {
    "attendance": """
SELECT e.emp_id, e.name, a.status, COUNT(a.id) AS days,
       MIN(date(a."date")) AS first_date, MAX(date(a."date")) AS last_date
FROM employees e LEFT JOIN attendance a ON a.emp_id = e.emp_id
WHERE CAST(e.emp_id AS TEXT) = CAST(:id AS TEXT)
GROUP BY e.emp_id, e.name, a.status""",
    "hierarchy": """
SELECT e.employee_number, e.employee_name, e.designation, e.manager_id,
       m.employee_name AS manager_name, e.location, e.email_address,
       e.date_of_joining
FROM employees e LEFT JOIN employees m ON m.employee_number = e.manager_id
WHERE CAST(e.employee_number AS TEXT) = CAST(:id AS TEXT)""",
    "odc": """
WITH ids AS (
  SELECT emp_id FROM odc_employees WHERE emp_id IS NOT NULL
  UNION
  SELECT emp_id FROM odc_logs WHERE emp_id IS NOT NULL
)
SELECT ids.emp_id, r.name, r.location, r.project_name, r.pm_name,
       COUNT(DISTINCT date(l.log_date)) AS odc_working_days
FROM ids
LEFT JOIN odc_employees r ON CAST(r.emp_id AS TEXT) = CAST(ids.emp_id AS TEXT)
LEFT JOIN odc_logs l ON CAST(l.emp_id AS TEXT) = CAST(ids.emp_id AS TEXT)
WHERE CAST(ids.emp_id AS TEXT) = CAST(:id AS TEXT)
GROUP BY ids.emp_id, r.name, r.location, r.project_name, r.pm_name""",
}

REPORTS_TEMPLATE = """
SELECT e.employee_number, e.employee_name, e.designation, e.location
FROM employees e
WHERE CAST(e.manager_id AS TEXT) = CAST(:id AS TEXT)
ORDER BY e.employee_name"""

NAME_LOOKUP_TEMPLATES = {
    "attendance": """
SELECT emp_id, name
FROM employees
WHERE LOWER(TRIM(name)) = LOWER(TRIM(:name))
   OR LOWER(TRIM(name)) LIKE LOWER('%' || TRIM(:name) || '%')
LIMIT 100""",
    "hierarchy": """
SELECT employee_number AS emp_id, employee_name AS name, designation,
       manager_id, location, email_address, date_of_joining
FROM employees
WHERE LOWER(TRIM(employee_name)) = LOWER(TRIM(:name))
   OR LOWER(TRIM(employee_name)) LIKE LOWER('%' || TRIM(:name) || '%')
LIMIT 100""",
    "odc": """
SELECT emp_id, name, location, project_name, pm_name
FROM odc_employees
WHERE LOWER(TRIM(name)) = LOWER(TRIM(:name))
   OR LOWER(TRIM(name)) LIKE LOWER('%' || TRIM(:name) || '%')
LIMIT 100""",
}


def build_prompt(module, question, schema, date_context, employee_ids, error=None, previous_sql=None):
    ids = ""
    if employee_ids and module != "meeting":
        ids = f"\nEMPLOYEE ID(S) MENTIONED: {', '.join(employee_ids)}\n"
    repair = ""
    if error:
        repair = (
            f"\nYOUR PREVIOUS QUERY FAILED.\nPrevious query:\n{previous_sql}\n"
            f"SQLite error: {error}\nWrite a corrected query.\n"
        )
    return f"""You write one SQLite SELECT query for {DESCRIPTIONS[module]}.

SCHEMA:
{schema}

DATE CONTEXT:
{date_context}
{ids}
QUESTION:
{question}
{repair}
RULES:
{COMMON_RULES}
{MODULE_RULES[module]}

EXAMPLES (adapt them to the question and the real schema; do not copy values blindly):
{EXAMPLES[module]}
"""


def _plan_and_run(module, question, schema, date_context, employee_ids):
    prompt = build_prompt(module, question, schema, date_context, employee_ids)
    sql = extract_sql(call_llm(prompt, num_predict=400))
    for attempt in (1, 2):
        try:
            return execute_select(module, sql), sql
        except (SQLExecutionError, UnsafeSQL) as exc:
            if attempt == 2:
                raise
            log.info("%s SQL failed (%s); asking the model to repair it", module, exc)
            repair = build_prompt(
                module, question, schema, date_context, employee_ids,
                error=str(exc), previous_sql=sql,
            )
            sql = extract_sql(call_llm(repair, num_predict=400))


REPORTS_TEMPLATE = """
SELECT e.employee_number, e.employee_name, e.designation, e.location
FROM employees e
WHERE CAST(e.manager_id AS TEXT) = CAST(:id AS TEXT)
ORDER BY e.employee_name"""
REPORTS_RE = re.compile(r"\b(reports? to|reporting to|direct reports?|team|subordinates?|who reports)\b", re.I)

# Same calculation as the ODC dashboard: one working day = one employee + one date.
ODC_OVERVIEW_SQL = """
WITH days AS (
  SELECT emp_id, date(log_date) AS d FROM odc_logs
  WHERE log_date IS NOT NULL AND TRIM(COALESCE(emp_id, '')) <> ''
  GROUP BY emp_id, date(log_date)
), people AS (
  SELECT emp_id FROM odc_employees WHERE TRIM(COALESCE(emp_id, '')) <> ''
  UNION
  SELECT emp_id FROM days
)
SELECT (SELECT COUNT(*) FROM days) AS total_odc_working_days,
       (SELECT COUNT(*) FROM people) AS total_employees,
       ROUND(1.0 * (SELECT COUNT(*) FROM days)
             / NULLIF((SELECT COUNT(*) FROM people), 0), 1) AS average_working_days,
       (SELECT MIN(d) FROM days) AS first_date,
       (SELECT MAX(d) FROM days) AS last_date"""
ODC_OVERVIEW_RE = re.compile(r"\b(total|overall|overview|summary|average)\b", re.I)
ODC_NOT_OVERVIEW = re.compile(
    r"\b(each|every|per|by|who|which|name|list|highest|lowest|top|compare|"
    r"jan\w*|feb\w*|mar\w*|apr\w*|may|jun\w*|jul\w*|aug\w*|sep\w*|oct\w*|nov\w*|dec\w*|"
    r"this month|last month|this year)\b|\b(19|20)\d{2}\b",
    re.I,
)


def _run_id_lookup(module, employee_ids, template=None):
    merged = None
    for emp_id in employee_ids[:3]:
        data = execute_select(module, template or ID_TEMPLATES[module], {"id": emp_id})
        if merged is None:
            merged = data
        else:
            merged["rows"].extend(data["rows"])
            merged["row_count"] = len(merged["rows"])
    return merged


# Questions that only identify an employee ("find employee 123", "name the employee
# with emp id 123") are answered straight from the database, with no LLM involved.
LOOKUP_BLOCKERS = re.compile(
    r"\b(absent|present|wfh|leave|late|attendance|days?|month|week|today|yesterday|"
    r"summary|percent\w*|how many|count|total|average|reports?|team|subordinates?|"
    r"between|since|until|compare|meetings?|tasks?)\b|\d{4}-\d{2}-\d{2}",
    re.I,
)


def run_module_agent(module: str, question: str, employee_ids=None, employee_names=None) -> dict:
    """Never raises: failures are reported through the 'error' code."""
    employee_ids = list(employee_ids or [])
    employee_names = list(employee_names or [])
    result = {"module": module, "sql": None, "data": None, "error": None}

    if employee_names and module in NAME_LOOKUP_TEMPLATES:
        try:
            merged = None
            for name in employee_names:
                data = execute_select(module, NAME_LOOKUP_TEMPLATES[module], {"name": name})
                if merged is None:
                    merged = data
                else:
                    merged["rows"].extend(data["rows"])
                    merged["row_count"] = len(merged["rows"])
            if merged:
                return {"module": module, "sql": "employee name lookup", "data": merged, "error": None}
        except (DatabaseUnavailable, SQLExecutionError, UnsafeSQL) as exc:
            log.warning("%s name lookup failed: %s", module, exc)
            result["error"] = "database_unavailable" if isinstance(exc, DatabaseUnavailable) else "query_failed"

    if employee_ids and module in ID_TEMPLATES and not LOOKUP_BLOCKERS.search(question):
        try:
            result.update(data=_run_id_lookup(module, employee_ids), sql="employee id lookup")
            return result
        except DatabaseUnavailable as exc:
            log.warning("%s database unavailable: %s", module, exc)
            result["error"] = "database_unavailable"
            return result
        except (SQLExecutionError, UnsafeSQL) as exc:
            log.warning("%s id lookup failed, trying the planner: %s", module, exc)

    # Exact answers for common questions; no LLM involved.
    if module == "hierarchy" and employee_ids and REPORTS_RE.search(question):
        try:
            result.update(
                data=_run_id_lookup(module, employee_ids, REPORTS_TEMPLATE),
                sql="direct reports lookup",
            )
            return result
        except (DatabaseUnavailable, SQLExecutionError, UnsafeSQL) as exc:
            log.warning("direct reports lookup failed, trying the planner: %s", exc)

    if (module == "odc" and not employee_ids
            and ODC_OVERVIEW_RE.search(question) and not ODC_NOT_OVERVIEW.search(question)):
        try:
            result.update(data=execute_select("odc", ODC_OVERVIEW_SQL), sql="odc overview")
            return result
        except DatabaseUnavailable:
            result["error"] = "database_unavailable"
            return result
        except (SQLExecutionError, UnsafeSQL) as exc:
            log.warning("odc overview failed, trying the planner: %s", exc)

    try:
        schema = get_module_schema(module)
        date_context = get_date_context()
        data, sql = _plan_and_run(module, question, schema, date_context, employee_ids)
        result.update(data=data, sql=sql)
    except LLMUnavailable:
        result["error"] = "llm_unavailable"
    except DatabaseUnavailable as exc:
        log.warning("%s database unavailable: %s", module, exc)
        result["error"] = "database_unavailable"
    except (SQLExecutionError, UnsafeSQL, ValueError) as exc:
        log.warning("%s query failed: %s", module, exc)
        result["error"] = "query_failed"

    return _finish(module, question, employee_ids, result)


def _finish(module, question, employee_ids, result):
    # Deterministic employee-ID lookup when the planner failed or found nothing.
    has_rows = bool(result["data"] and result["data"]["rows"])
    if (
        employee_ids
        and module in ID_TEMPLATES
        and not has_rows
        and result["error"] in (None, "query_failed", "llm_unavailable")
    ):
        try:
            data = _run_id_lookup(module, employee_ids)
            result.update(data=data, sql="employee id lookup", error=None)
        except (DatabaseUnavailable, SQLExecutionError, UnsafeSQL) as exc:
            log.warning("%s id lookup failed: %s", module, exc)

    return result