import json
import re

try:
    import dateparser
except ImportError:
    dateparser = None

from app.chatbot.agents.sql_agent import call_llm, LLMUnavailable


EMPLOYEE_ID_RE = re.compile(r"\b((?:EMP|E)[-_]?\d{2,}|ABC\d{2,}|[A-Z]{2,}\d{2,})\b", re.I)
PERSON_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b")
PRIORITY_RE = re.compile(r"\b(high|medium|low)[-\s]?priority\b|\bpriority\s*[:=-]?\s*(high|medium|low)\b", re.I)
DEADLINE_RE = re.compile(
    r"(?i)(?:by|before|within|due on|deadline(?: is)?|complete .*? by|submit .*? by|finish .*? by)\s+([^.!?]+)",
)


def extract_json(text: str):
    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL,
    )

    if not match:
        raise ValueError("Gemma did not return valid JSON.")

    return json.loads(match.group(0))


def _normalize_priority(text: str) -> str:
    match = PRIORITY_RE.search(text or "")
    if not match:
        return "Not specified"
    value = next((group for group in match.groups() if group), "")
    return value.title() if value.lower() in ("high", "medium", "low") else "Not specified"


def _normalize_deadline(deadline_text: str) -> str | None:
    deadline_text = (deadline_text or "").strip()
    if not deadline_text:
        return None
    if dateparser:
        parsed = dateparser.parse(deadline_text, settings={"PREFER_DATES_FROM": "future"})
        if parsed:
            return parsed.strftime("%Y-%m-%d")
    return None


def _deduplicate_tasks(tasks: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for task in tasks:
        key = (
            str(task.get("owner", "Unknown")).strip().casefold(),
            str(task.get("task", "")).strip().casefold(),
            str(task.get("deadline_text", "Not specified")).strip().casefold(),
        )
        if not task.get("task") or key in seen:
            continue
        seen.add(key)
        unique.append(task)
    return unique


def _regex_extract(transcript: str) -> dict:
    tasks = []
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", transcript) if sentence.strip()]

    assignment_re = re.compile(
        r"(?P<owner>[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})"
        r"(?:,?\s*(?:employee\s*(?:id|number)?\s*[:#]?\s*(?P<employee_id>EMP[-_]?\d+|E[-_]?\d+|ABC\d+|[A-Z]{2,}\d+))?\,?)"
        r"\s+(?:will|should|needs to|must|is responsible for|responsible for|,)?\s*(?P<task>[^.!?]+)",
        re.I,
    )

    assignment_re_fallback = re.compile(
        r"(?:assign(?: the task)?\s+)?(?:the\s+)?(?P<task>[^.!?]+?)\s+(?:to|for)\s+(?P<owner>[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
        re.I,
    )

    for sentence in sentences:
        employee_match = EMPLOYEE_ID_RE.search(sentence)
        employee_id = employee_match.group(1).upper() if employee_match else "Not specified"

        match = assignment_re.search(sentence)
        if not match:
            match = assignment_re_fallback.search(sentence)

        if match:
            groups = match.groupdict()
            owner = groups.get("owner") or "Unknown"
            task = groups.get("task") or ""
            if not task:
                continue

            deadline_match = re.search(r"(?:by|before|within|due on|deadline(?: is)?)[^.!?]*", sentence, re.I)
            deadline_text = deadline_match.group(0).strip() if deadline_match else "Not specified"
            if deadline_match:
                deadline_text = re.sub(r"^(?:by|before|within|due on|deadline(?: is)?)[\s:-]*", "", deadline_text, flags=re.I).strip() or deadline_match.group(0).strip()

            tasks.append({
                "owner": owner.strip() if owner != "Unknown" else "Unknown",
                "employee_id": employee_id,
                "task": task.strip().rstrip(","),
                "deadline_text": deadline_text,
                "deadline_date": _normalize_deadline(deadline_text),
                "priority": _normalize_priority(sentence),
                "status": "Pending",
            })

    decisions = []
    decision_re = re.compile(r"(?:we decided|decided to|decision(?: is)?|agreed to|approved)\s+([^.!?]+)", re.I)
    for match in decision_re.finditer(transcript):
        decision = match.group(1).strip()
        if decision and decision not in decisions:
            decisions.append(decision)

    return {"summary": "", "decisions": decisions, "tasks": _deduplicate_tasks(tasks)}


def process_transcript(transcript: str) -> dict:
    if not transcript or not transcript.strip():
        raise ValueError("Transcript is empty.")

    deterministic = _regex_extract(transcript)

    prompt = f"""
Analyze this meeting transcript.

TRANSCRIPT:
{transcript[:12000]}

Return valid JSON with this exact structure:
{{
  "summary": "short meeting summary",
  "decisions": ["decision 1"],
  "tasks": [{{
    "owner": "person name or Unknown",
    "employee_id": "EMP102 or Not specified",
    "task": "action description",
    "deadline_text": "deadline mentioned or Not specified",
    "deadline_date": "YYYY-MM-DD or null",
    "priority": "High, Medium, Low, or Not specified"
  }}]
}}

Rules:
- Do not invent people, decisions, deadlines or tasks.
- Use Unknown when the owner is not clear.
- Use Not specified when no value is available.
- Return JSON only.
"""

    llm_result = None
    try:
        llm_result = extract_json(call_llm(prompt, num_predict=700))
    except (LLMUnavailable, ValueError, json.JSONDecodeError):
        llm_result = None

    if llm_result:
        llm_tasks = llm_result.get("tasks") if isinstance(llm_result.get("tasks"), list) else []
        merged_tasks = list(deterministic["tasks"])
        for llm_task in llm_tasks:
            if not isinstance(llm_task, dict):
                continue
            normalized = {
                "owner": llm_task.get("owner") or "Unknown",
                "employee_id": llm_task.get("employee_id") or "Not specified",
                "task": llm_task.get("task") or "",
                "deadline_text": llm_task.get("deadline_text") or "Not specified",
                "deadline_date": llm_task.get("deadline_date") or None,
                "priority": llm_task.get("priority") or "Not specified",
                "status": "Pending",
            }
            if normalized["employee_id"] == "":
                normalized["employee_id"] = "Not specified"
            if normalized["employee_id"] != "Not specified":
                normalized["employee_id"] = normalized["employee_id"].upper()
            merged_tasks.append(normalized)

        merged_decisions = []
        for decision in (llm_result.get("decisions") or []) + deterministic["decisions"]:
            if isinstance(decision, str) and decision.strip() and decision.strip() not in merged_decisions:
                merged_decisions.append(decision.strip())

        return {
            "summary": llm_result.get("summary") or "",
            "decisions": merged_decisions,
            "tasks": _deduplicate_tasks(merged_tasks),
        }

    return {
        "summary": transcript[:500],
        "decisions": deterministic["decisions"],
        "tasks": deterministic["tasks"],
    }
