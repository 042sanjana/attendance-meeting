"""Question routing: the local LLM decides which modules are needed.
Keyword matching is only a safety net (LLM down / unusable answer)."""
import json
import logging
import re

from app.chatbot.agents.sql_agent import LLMUnavailable, call_llm
from app.chatbot.tools.schema_discovery import find_employee_ids_in_text

log = logging.getLogger(__name__)

VALID = ("attendance", "hierarchy", "odc", "meeting")

STRONG = {
    "attendance": r"\battendance\b",
    "hierarchy": r"\bhierarchy\b|\borg(?:anization|anisation)?(?:al)? chart\b",
    "odc": r"\bodc\b",
    "meeting": r"\bmeetings?\b|\btranscripts?\b|\baction items?\b|\bminutes\b",
}

BROAD = {
    "attendance": r"\b(present|absent|wfh|work from home|half[- ]?day|check[- ]?in|check[- ]?out|late|leave|attendance percentage|working from home)\b",
    "hierarchy": r"\b(manager|managers|reports? to|reporting|direct reports?|designation|team members?|subordinates?|employee details|location)\b",
    "odc": r"\b(onsite|offshore|working days|lob|delivery manager|dm name|project location|project-wise|location-wise)\b",
    "meeting": r"\b(decisions?|tasks?|deadlines?|owner|recording|summar(?:y|ize|ise)|pending)\b",
}


def extract_employee_ids(text: str) -> list[str]:
    """Extract IDs from the question and confirm them against the live databases."""
    return find_employee_ids_in_text(text)


def _match(patterns: dict, q: str) -> set[str]:
    return {module for module, pattern in patterns.items() if re.search(pattern, q, re.I)}


ROUTER_PROMPT = """Decide which data modules are needed to answer the question.

Modules:
- attendance: daily attendance per employee (present, absent, WFH, leave, check-in/out times, attendance percentages)
- hierarchy: organization chart (employee names, designation, manager, who reports to whom, location, joining date, email)
- odc: ODC tracker (ODC working days, ODC roster, project, PM, delivery manager)
- meeting: meeting notes (summaries, transcripts, decisions, action items/tasks, owners, deadlines)

Rules:
- Select every module needed.
- A question that only identifies an employee needs attendance, hierarchy and odc.
- Return JSON only, for example {{"modules": ["attendance", "odc"]}}

QUESTION: {question}
JSON:"""


def _llm_modules(question: str) -> set[str] | None:
    try:
        text = call_llm(ROUTER_PROMPT.format(question=question), num_predict=80)
    except LLMUnavailable:
        return None
    match = re.search(r"\{.*?\}", text, re.S)
    if not match:
        return None
    try:
        modules = json.loads(match.group(0)).get("modules", [])
    except (ValueError, AttributeError):
        return None
    return {module for module in modules if module in VALID} or None


def route_question(question: str, employee_ids: list[str] | None = None) -> list[str]:
    ids = employee_ids if employee_ids is not None else extract_employee_ids(question)
    strong = _match(STRONG, question)
    broad = _match(BROAD, question)

    if ids:
        chosen = set(strong)
        q = question.lower()
        explicit_all = any(word in q for word in ("all information", "details", "employee information", "find employee", "show employee"))
        if explicit_all:
            chosen |= {"attendance", "hierarchy", "odc"}
        else:
            chosen |= broad
            if not chosen:
                chosen = {"attendance", "hierarchy", "odc"}
    else:
        llm = _llm_modules(question)
        chosen = strong | (llm if llm is not None else broad)
        if not chosen and re.search(r"\b(employees?|staff|people|everyone)\b", question, re.I):
            chosen = {"attendance", "hierarchy", "odc"}

    return [module for module in VALID if module in chosen]