import json
import logging
import re

from app.chatbot.agents.sql_agent import call_llm
from app.chatbot.tools.schema_discovery import get_date_context

log = logging.getLogger(__name__)

LABELS = {
    "attendance": "Attendance",
    "hierarchy": "Organization Hierarchy",
    "odc": "ODC Tracker",
    "meeting": "Meeting Notes",
}
MAX_EVIDENCE_CHARS = 6000
MAX_CELL = 300


def friendly_error(code: str) -> str:
    return {
        "llm_unavailable": "the local AI model did not respond in time",
        "database_unavailable": "that data source is not available right now",
    }.get(code, "the data could not be retrieved for this question")


def collect_results(state) -> list[dict]:
    out = []
    for module in LABELS:
        res = state.get(f"{module}_result")
        if not res:
            continue
        data = res.get("data") or {}
        out.append({
            "module": module,
            "label": LABELS[module],
            "columns": data.get("columns", []),
            "rows": data.get("rows", []),
            "row_count": data.get("row_count", 0),
            "truncated": data.get("truncated", False),
            "error": res.get("error"),
            "sql": res.get("sql"),
        })
    return out


def _clip(v, n=MAX_CELL):
    return v[:n] + "…" if isinstance(v, str) and len(v) > n else v


def ui_tables(summaries):
    return [
        {
            "title": s["label"],
            "columns": s["columns"],
            "rows": [[_clip(v) for v in row] for row in s["rows"]],
            "truncated": s["truncated"],
        }
        for s in summaries if s["rows"] and not s["error"]
    ]


def ui_sources(summaries, has_rag):
    sources = []
    for s in summaries:
        if s["error"]:
            continue
        plus = "+" if s["truncated"] else ""
        sources.append({
            "module": s["module"],
            "label": s["label"],
            "description": f"{s['row_count']}{plus} record(s) retrieved",
        })
    if has_rag:
        sources.append({
            "module": "meeting_transcripts",
            "label": "Meeting Transcripts",
            "description": "Transcript passages retrieved",
        })
    return sources


def _evidence(summaries, rag_text, preview):
    ev = {}
    for s in summaries:
        if s["error"]:
            continue
        ev[s["label"]] = {
            "row_count": s["row_count"],
            "more_rows_than_shown": s["truncated"] or s["row_count"] > preview,
            "rows": [
                dict(zip(s["columns"], (_clip(v, 200) for v in r)))
                for r in s["rows"][:preview]
            ],
        }
    if rag_text:
        ev["Meeting transcript passages"] = rag_text[:2500]
    return ev


CUT_RE = re.compile(
    r"^\W*(explanation|explanations|calculations?|how (i|this|it)|methodology|"
    r"notes? on|attendance days vs|analysis of the (query|sql))\b",
    re.I,
)
SQLISH = re.compile(
    r"\b(select|group by|where clause|limit \d+|count\(\*\)|sql|query)\b", re.I
)


def clean_answer(text: str) -> str:
    """Removes code blocks, SQL, pipe tables and 'explanation' sections."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    kept = []
    for line in text.splitlines():
        s = line.strip()
        if CUT_RE.match(s):
            break  # drop everything from the explanation section onwards
        if "|" in s or SQLISH.search(s):
            continue
        if re.match(r"^[-=_]{3,}$", s):
            continue
        kept.append(line.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()


def fallback_answer(summaries, problems) -> str:
    lines = ["Here is what I found:"]
    for s in summaries:
        if not s["error"]:
            plus = "+" if s["truncated"] else ""
            lines.append(
                f"- **{s['label']}**: {s['row_count']}{plus} record(s). See the table below."
            )
    lines += [f"- Note: {p}." for p in problems]
    return "\n".join(lines)


def no_records_answer(problems, date_context) -> str:
    if problems:
        return (
            "I could not complete this lookup: " + "; ".join(problems) + ". "
            "Please check that the backend and the Ollama model are running, then try again."
        )
    ranges = [l for l in date_context.splitlines() if "records exist" in l]
    msg = "I did not find any matching records for that question."
    if ranges:
        msg += "\n\nAvailable data:\n" + "\n".join(f"- {r}" for r in ranges)
    return msg


def run_analyst_agent(question, summaries, rag_text, problems, date_context) -> str:
    text = "{}"
    for preview in (25, 12, 6, 3):
        evidence = _evidence(summaries, rag_text, preview)
        text = json.dumps(evidence, default=str, ensure_ascii=False)
        if len(text) <= MAX_EVIDENCE_CHARS:
            break

    issues = "\n".join(f"- {p}" for p in problems) or "None"
    prompt = f"""You are a workforce analytics assistant writing the final reply to an HR manager.

QUESTION:
{question}

DATE CONTEXT:
{date_context}

DATA RETRIEVED (JSON):
{text}

ISSUES:
{issues}

Write a clear, friendly answer in Markdown.
Rules:
1. Use only the data above. Never invent names, numbers, percentages or dates.
2. Start with the direct answer in one or two sentences, including the actual names/numbers.
3. Use short ### headings and bullet lists only when they help.
4. Do NOT write tables, pipe characters, SQL, JSON or code blocks. Full tables are shown separately below your answer, so say "details are in the table below" when there are rows.
5. If more than 10 rows exist, name only the top few and refer to the table.
6. Attendance days and ODC working days are different things; do not mix them.
7. Meeting task owners are names, not employee IDs. Only match people across modules when names are identical, and say when matching is not possible.
8. If a topic returned no rows, say no matching records were found.
9. If the date used differs from today's date (see DATE CONTEXT), say which date the answer is for.
10. Mention listed ISSUES plainly, without technical detail.
11. Never mention SQL, queries, prompts or database internals."""

    answer = clean_answer(call_llm(prompt, num_predict=700))
    if not answer:
        raise ValueError("Empty answer")
    return answer


def _key(value) -> str:
    return str(value or "").strip().lstrip("0")


def lookup_answer(summaries, employee_ids, problems) -> str:
    """Exact, model-free answer for 'find / name employee <id>' questions."""
    people: dict[str, dict] = {}
    for s in summaries:
        if s["error"]:
            continue
        for row in s["rows"]:
            rec = dict(zip(s["columns"], row))
            emp_id = rec.get("emp_id") or rec.get("employee_number")
            if not emp_id:
                continue
            p = people.setdefault(_key(emp_id), {"id": emp_id, "name": None, "lines": {}})
            p["name"] = p["name"] or rec.get("name") or rec.get("employee_name")
            if s["module"] == "attendance":
                att = p["lines"].setdefault("attendance", {"counts": [], "first": None, "last": None})
                if rec.get("status"):
                    att["counts"].append(f"{rec['status']}: {rec.get('days')} day(s)")
                    att["first"] = min(filter(None, [att["first"], rec.get("first_date")]), default=None)
                    att["last"] = max(filter(None, [att["last"], rec.get("last_date")]), default=None)
            else:
                p["lines"][s["module"]] = rec

    if not people:
        text = "No employee with ID " + ", ".join(employee_ids) + " was found in the connected records."
    else:
        blocks = []
        for p in people.values():
            name = p["name"] or "(name not available)"
            lines = [f"Employee ID **{p['id']}** is **{name}**."]
            h = p["lines"].get("hierarchy")
            if h:
                if h.get("designation"):
                    lines.append(f"- Designation: {h['designation']}")
                if h.get("manager_name") or h.get("manager_id"):
                    lines.append(f"- Manager: {h.get('manager_name') or 'name not available'} (ID {h.get('manager_id')})")
                if h.get("location"):
                    lines.append(f"- Location: {h['location']}")
                if h.get("email_address"):
                    lines.append(f"- Email: {h['email_address']}")
                if h.get("date_of_joining"):
                    lines.append(f"- Date of joining: {h['date_of_joining']}")
            o = p["lines"].get("odc")
            if o:
                lines.append(f"- ODC working days: {o.get('odc_working_days', 0)}")
                if o.get("project_name"):
                    lines.append(f"- ODC project: {o['project_name']}")
                if o.get("pm_name"):
                    lines.append(f"- ODC PM: {o['pm_name']}")
            a = p["lines"].get("attendance")
            if a:
                if a["counts"]:
                    lines.append(f"- Attendance: {', '.join(a['counts'])} (records from {a['first']} to {a['last']})")
                else:
                    lines.append("- Attendance: no attendance records yet")
            blocks.append("\n".join(lines))
        text = "\n\n".join(blocks)
    if problems:
        text += "\n\n" + "\n".join(f"- Note: {p}." for p in problems)
    return text


def build_final(state) -> dict:
    summaries = collect_results(state)
    rag = state.get("rag_result") or ""
    has_rag = bool(rag) and not rag.startswith("No matching")
    problems = [
        f"{s['label']}: {friendly_error(s['error'])}" for s in summaries if s["error"]
    ]
    date_context = get_date_context()

    tables = ui_tables(summaries)
    sources = ui_sources(summaries, has_rag)
    has_rows = any(s["rows"] for s in summaries if not s["error"]) or has_rag

    if not summaries and not has_rag:
        answer = "I could not retrieve relevant records from the connected modules."
    elif not has_rows and not state.get("employee_ids"):
        answer = no_records_answer(problems, date_context)
    elif state.get("employee_ids") and all(
        s["sql"] == "employee id lookup" for s in summaries if not s["error"]
    ) and any(not s["error"] for s in summaries):
        answer = lookup_answer(summaries, state["employee_ids"], problems)
    elif not has_rows:
        answer = no_records_answer(problems, date_context)
    else:
        try:
            answer = run_analyst_agent(
                state["question"], summaries, rag if has_rag else "", problems, date_context
            )
        except Exception as exc:
            log.warning("Analyst LLM failed: %s", exc)
            answer = fallback_answer(summaries, problems)
            answer += (
                "\n\nNote: the AI model was slow to respond, "
                "so this is a direct summary of the records."
            )

    return {"answer": answer, "tables": tables, "sources": sources}