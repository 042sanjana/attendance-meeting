"""Safe, read-only SQLite access for the chatbot.

Defence in depth:
  1. the SQL text is validated (single SELECT/WITH statement),
  2. the database is opened read-only (mode=ro) and is never created if missing,
  3. a SQLite authorizer only allows reads of whitelisted tables,
  4. sensitive / bulky columns are returned as NULL,
  5. a time limit and a row limit are enforced.
"""
import logging
import re
import sqlite3
import time
from pathlib import Path

from app.chatbot import config

log = logging.getLogger(__name__)

MAX_ROWS = 200
MAX_SECONDS = 8
MAX_CELL_CHARS = 2000


class DatabaseUnavailable(Exception):
    """The database file is missing, empty or has none of the expected tables."""


class UnsafeSQL(Exception):
    """The generated SQL is not a single read-only SELECT."""


class SQLExecutionError(Exception):
    """SQLite rejected the query (bad column, syntax error, timeout ...)."""


SENSITIVE_TABLE = re.compile(r"^(users?|accounts?)$|password|token|credential", re.I)
SENSITIVE_COLUMN = re.compile(r"password|hash|token|secret", re.I)
HIDDEN_COLUMNS = {"raw_json"}  # large payload column in odc_logs

_FIXED_TABLES = {
    "attendance": ("employees", "attendance"),
    "odc": ("odc_employees", "odc_logs"),
    "hierarchy": ("employees",),
    "meeting": None,  # discovered from the file, minus sensitive tables
}


def db_path(module: str) -> str:
    paths = {
        "attendance": config.ATTENDANCE_DB,
        "odc": config.ODC_DB,
        "hierarchy": config.HIERARCHY_DB,
        "meeting": config.MEETING_DB,
    }
    if module not in paths:
        raise ValueError(f"Unknown module: {module}")
    return paths[module]


def hidden_column(name: str) -> bool:
    return bool(SENSITIVE_COLUMN.search(name)) or name.lower() in HIDDEN_COLUMNS


def connect(module: str) -> sqlite3.Connection:
    path = Path(db_path(module))
    if not path.is_file() or path.stat().st_size == 0:
        raise DatabaseUnavailable(f"{module} database not found at {path}")
    try:
        return sqlite3.connect(
            f"{path.resolve().as_uri()}?mode=ro",
            uri=True,
            timeout=10,
            check_same_thread=False,
        )
    except sqlite3.Error as exc:
        raise DatabaseUnavailable(str(exc)) from exc


def allowed_tables(module: str, conn: sqlite3.Connection) -> list[str]:
    existing = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'"
        )
    ]
    fixed = _FIXED_TABLES[module]
    if fixed is not None:
        return [t for t in existing if t in fixed]
    return [t for t in existing if not SENSITIVE_TABLE.search(t)]


_LITERALS = re.compile(r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"")
_COMMENTS = re.compile(r"--[^\n]*|/\*.*?\*/", re.S)
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|"
    r"vacuum|reindex|truncate|load_extension)\b",
    re.I,
)


def validate_select(sql: str) -> str:
    sql = (sql or "").strip().rstrip(";").strip()
    if not sql:
        raise UnsafeSQL("Empty query")
    cleaned = _COMMENTS.sub(" ", _LITERALS.sub("''", sql))
    if ";" in cleaned:
        raise UnsafeSQL("Only one statement is allowed")
    if not re.match(r"^\s*(select|with)\b", cleaned, re.I):
        raise UnsafeSQL("Only SELECT queries are allowed")
    if _FORBIDDEN.search(cleaned):
        raise UnsafeSQL("Query contains a forbidden keyword")
    return sql


_CTE_NAME = re.compile(
    r"(?:\bWITH\b|,)\s*(?:RECURSIVE\s+)?([A-Za-z_]\w*)\s*(?:\([^)]*\))?\s*AS\s*"
    r"(?:NOT\s+MATERIALIZED\s*|MATERIALIZED\s*)?\(",
    re.I,
)


def _cte_names(sql: str) -> set[str]:
    """Names declared by WITH ... AS (...) inside the query. SQLite reports reads
    of a CTE like reads of a table, so these names must be allowed explicitly."""
    return {m.lower() for m in _CTE_NAME.findall(_LITERALS.sub("''", sql))}


def _make_authorizer(tables: list[str], extra_names: set[str] | None = None):
    allowed = {t.lower() for t in tables} | (extra_names or set())
    ok_actions = {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_FUNCTION,
        sqlite3.SQLITE_RECURSIVE,
    }

    def authorizer(action, arg1, arg2, db_name, source):
        if action in ok_actions:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ:
            if (arg1 or "").lower() not in allowed:
                return sqlite3.SQLITE_DENY
            if arg2 and hidden_column(arg2):
                return sqlite3.SQLITE_IGNORE  # column is returned as NULL
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY

    return authorizer


def _cell(value, limit=MAX_CELL_CHARS):
    if isinstance(value, bytes):
        return "<binary>"
    if limit and isinstance(value, str) and len(value) > limit:
        return value[:limit] + "…"
    return value


def execute_select(
    module: str,
    sql: str,
    params: dict | None = None,
    max_rows: int = MAX_ROWS,
    max_cell: int | None = MAX_CELL_CHARS,
) -> dict:
    sql = validate_select(sql)
    conn = connect(module)
    try:
        try:
            tables = allowed_tables(module, conn)
        except sqlite3.Error as exc:
            raise DatabaseUnavailable(str(exc)) from exc
        if not tables:
            raise DatabaseUnavailable(f"No usable tables in the {module} database")

        conn.set_authorizer(_make_authorizer(tables, _cte_names(sql)))
        deadline = time.monotonic() + MAX_SECONDS
        conn.set_progress_handler(
            lambda: 1 if time.monotonic() > deadline else 0, 10000
        )
        try:
            cur = conn.execute(sql, params or {})
            columns = [d[0] for d in (cur.description or [])]
            fetched = cur.fetchmany(max_rows + 1)
        except sqlite3.Error as exc:
            raise SQLExecutionError(str(exc)) from exc

        truncated = len(fetched) > max_rows
        rows = [[_cell(v, max_cell) for v in r] for r in fetched[:max_rows]]
        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": truncated,
        }
    finally:
        conn.close()