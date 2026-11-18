
import sqlite3
from pathlib import Path

from app.chatbot.config import (
    ATTENDANCE_DB,
    HIERARCHY_DB,
    MEETING_DB,
    ODC_DB,
)


MODULE_DATABASES = {
    "attendance": ATTENDANCE_DB,
    "hierarchy": HIERARCHY_DB,
    "meeting": MEETING_DB,
    "odc": ODC_DB,
}

MODULE_TABLES = {
    "attendance": {"employees", "attendance", "upload_logs"},
    "hierarchy": {"employees"},
    "meeting": {"meetings", "tasks"},
    "odc": {
        "odc_employees",
        "odc_employee_remarks",
        "odc_logs",
        "odc_uploads",
    },
}


def get_connection(module: str):
    if module not in MODULE_DATABASES:
        raise ValueError("Invalid database module.")

    database_path = Path(MODULE_DATABASES[module])

    if not database_path.exists():
        raise FileNotFoundError(
            f"{module} database not found: {database_path}"
        )

    uri = database_path.resolve().as_uri() + "?mode=ro"

    conn = sqlite3.connect(
        uri,
        uri=True,
        timeout=15
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")

    return conn


def _authorizer(module: str):
    allowed_tables = MODULE_TABLES[module]

    def authorize(action, arg1, arg2, database, trigger):
        if action == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK

        if action == sqlite3.SQLITE_READ:
            if arg1 in allowed_tables:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY

        if action == sqlite3.SQLITE_FUNCTION:
            return sqlite3.SQLITE_OK

        if hasattr(sqlite3, "SQLITE_RECURSIVE"):
            if action == sqlite3.SQLITE_RECURSIVE:
                return sqlite3.SQLITE_OK

        return sqlite3.SQLITE_DENY

    return authorize


def execute_select(module: str, sql: str, limit: int = 200):
    if module not in MODULE_TABLES:
        raise ValueError("Invalid module.")

    if not isinstance(sql, str):
        raise ValueError("SQL must be text.")

    sql = sql.strip()

    if not sql.lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")

    # Disallow multiple statements.
    if ";" in sql.rstrip(";"):
        raise ValueError("Multiple SQL statements are not allowed.")

    conn = get_connection(module)

    try:
        conn.set_authorizer(_authorizer(module))

        # The outer limit protects the response size.
        wrapped_sql = (
            f"SELECT * FROM ({sql.rstrip(';')}) "
            f"AS chatbot_result LIMIT {int(limit)}"
        )

        rows = conn.execute(wrapped_sql).fetchall()

        return {
            "columns": (
                list(rows[0].keys())
                if rows
                else []
            ),
            "rows": [dict(row) for row in rows],
            "row_count": len(rows),
        }

    finally:
        conn.close()
