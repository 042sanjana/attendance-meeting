"""Discovers the REAL schema and date coverage from the SQLite files."""
import calendar
import logging
import re
import threading
import time
from datetime import date, datetime

from app.chatbot.tools.sql_executor import (
    db_path,
    DatabaseUnavailable,
    SQLExecutionError,
    allowed_tables,
    connect,
    execute_select,
    hidden_column,
)

log = logging.getLogger(__name__)

_TTL = 20  # short, so a fresh Excel upload is seen quickly
_lock = threading.Lock()
_schema_cache: dict[str, tuple[float, str]] = {}
_date_cache: tuple[float, str] | None = None

LONG_TEXT = re.compile(
    r"transcript|summary|text|json|content|description|remarks|notes|body", re.I
)

MODULE_NOTES = {
    "attendance": (
        "NOTES: attendance has ONE row per employee per date (unique emp_id + date). "
        "Join attendance.emp_id = employees.emp_id to get names. "
        "Use the exact status values listed above."
    ),
    "odc": (
        "NOTES: odc_employees is the ODC roster. odc_logs holds date-level records "
        "(several LOB / DM rows can exist for the same employee and date). "
        "Join on emp_id."
    ),
    "hierarchy": (
        "NOTES: employee_number is the employee identifier. manager_id holds the "
        "manager's employee_number (self join: m.employee_number = e.manager_id). "
        "There is no department column; use designation or location."
    ),
    "meeting": (
        "NOTES: transcripts and summaries are long text. Tasks may be stored as JSON "
        "text inside the meetings table or in a separate tasks table; use whatever "
        "exists above. Task owners are person names, not employee IDs."
    ),
}


def _describe_table(conn, table: str) -> str:
    cols = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
    lines = [f"TABLE {table} ({count} rows)"]
    visible = []
    for _cid, name, ctype, _nn, _default, pk in cols:
        if hidden_column(name):
            continue
        visible.append(name)
        line = f"  - {name} {ctype or 'TEXT'}" + (" PRIMARY KEY" if pk else "")
        if count and not LONG_TEXT.search(name) and (ctype or "").upper() != "BLOB":
            vals = [
                r[0]
                for r in conn.execute(
                    f'SELECT DISTINCT "{name}" FROM "{table}" '
                    f'WHERE "{name}" IS NOT NULL LIMIT 13'
                )
            ]
            if 0 < len(vals) <= 12 and all(isinstance(v, (str, int)) for v in vals):
                line += " -- values: " + ", ".join(repr(v) for v in vals)
        lines.append(line)

    if count:
        cur = conn.execute(f'SELECT * FROM "{table}" LIMIT 1')
        names = [d[0] for d in cur.description]
        row = cur.fetchone()
        example = {
            n: (str(v)[:80] if v is not None else None)
            for n, v in zip(names, row)
            if n in visible
        }
        lines.append(f"  example row: {example}")
    return "\n".join(lines)


def get_module_schema(module: str) -> str:
    now = time.time()
    with _lock:
        cached = _schema_cache.get(module)
        if cached and now - cached[0] < _TTL:
            return cached[1]

    conn = connect(module)  # raises DatabaseUnavailable
    try:
        tables = allowed_tables(module, conn)
        if not tables:
            raise DatabaseUnavailable(f"No usable tables in the {module} database")
        text = "\n\n".join(_describe_table(conn, t) for t in tables)
    finally:
        conn.close()

    text += "\n\n" + MODULE_NOTES.get(module, "")
    with _lock:
        _schema_cache[module] = (now, text)
    return text


def _row(module: str, sql: str, params: dict | None = None):
    return execute_select(module, sql, params)["rows"][0]


def get_date_context() -> str:
    """Tells the model what 'today' and 'this month' mean for the data we hold."""
    global _date_cache
    now = time.time()
    with _lock:
        if _date_cache and now - _date_cache[0] < 10:
            return _date_cache[1]

    today = date.today()
    lines = [f"Today's calendar date: {today.isoformat()} ({today.strftime('%A')})."]

    try:
        mn, mx, cnt = _row(
            "attendance",
            'SELECT MIN(date("date")), MAX(date("date")), COUNT(*) FROM attendance WHERE date("date") IS NOT NULL',
        )
        if cnt:
            has_today = _row(
                "attendance",
                'SELECT COUNT(*) FROM attendance WHERE date("date") = :d',
                {"d": today.isoformat()},
            )[0]
            lines.append(
                f"Attendance: records exist from {mn} to {mx} "
                f"({cnt} rows; latest date with records: {mx})."
            )
            if has_today:
                effective = today.isoformat()
                lines.append(f"For 'today' in attendance questions use the date '{effective}'.")
            else:
                effective = str(mx)[:10]
                lines.append(
                    f"No attendance rows exist for today ({today.isoformat()}). "
                    f"For 'today' use the latest available date '{effective}' "
                    "and tell the user that this is the latest date with data."
                )
            eff = datetime.strptime(effective, "%Y-%m-%d")
            last_day = calendar.monthrange(eff.year, eff.month)[1]
            lines.append(
                "For 'this month' in attendance questions use "
                f"date(\"date\") BETWEEN '{eff.year}-{eff.month:02d}-01' AND "
                f"'{eff.year}-{eff.month:02d}-{last_day:02d}'."
            )
        else:
            lines.append("Attendance: no attendance records exist yet.")
    except (DatabaseUnavailable, SQLExecutionError, ValueError) as exc:
        log.warning("Attendance date context unavailable: %s", exc)
        lines.append("Attendance: data source unavailable.")

    try:
        mn, mx, cnt = _row(
            "odc", "SELECT MIN(date(log_date)), MAX(date(log_date)), COUNT(*) FROM odc_logs"
        )
        if cnt:
            lines.append(f"ODC: records exist from {mn} to {mx} ({cnt} log rows).")
        else:
            lines.append("ODC: no log records exist yet.")
    except (DatabaseUnavailable, SQLExecutionError) as exc:
        log.warning("ODC date context unavailable: %s", exc)
        lines.append("ODC: data source unavailable.")

    text = "\n".join(lines)
    with _lock:
        _date_cache = (now, text)
    return text


def diagnostics() -> dict:
    """What the chatbot is really reading (paths, tables, row counts, statuses, dates)."""
    out = {}
    for module in ("attendance", "hierarchy", "odc", "meeting"):
        info = {"path": db_path(module)}
        try:
            conn = connect(module)
            try:
                tables = allowed_tables(module, conn)
                info["tables"] = {
                    t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                    for t in tables
                }
            finally:
                conn.close()
        except DatabaseUnavailable as exc:
            info["error"] = str(exc)
        out[module] = info
    try:
        rows = execute_select(
            "attendance", "SELECT status, COUNT(*) AS rows_count FROM attendance GROUP BY status"
        )["rows"]
        out["attendance_status_counts"] = {str(r[0]): r[1] for r in rows}
    except Exception as exc:  # diagnostics must never crash
        out["attendance_status_counts"] = f"unavailable: {exc}"
    out["date_context"] = get_date_context().splitlines()
    return out