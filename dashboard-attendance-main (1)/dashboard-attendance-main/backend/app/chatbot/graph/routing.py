"""Question routing: the local LLM decides which modules are needed.
Keyword matching is only a safety net (LLM down / unusable answer)."""
import json
import logging
import re

from app.chatbot.agents.sql_agent import LLMUnavailable, call_llm

log = logging.getLogger(__name__)

VALID = ("attendance", "hierarchy", "odc", "meeting")
ID_RE = re.compile(r"(?<![\w.-])\d{5,10}(?![\w-])")

# Words that unambiguously name a module (always honoured).
STRONG = {
    "attendance": r"\battendance\b",
    "hierarchy": r"\bhierarchy\b|\borg(?:anization|anisation)?(?:al)? chart\b",
    "odc": r"\bodc\b",
    "meeting": r"\bmeetings?\b|\btranscripts?\b|\baction items?\b|\bminutes\b",
}

# Broader vocabulary, used only when the LLM cannot route.
BROAD = {
    "attendance": r"\b(present|absent|wfh|work from home|half[- ]?day|check[- ]?in|check[- ]?out|late|leave)\b",
    "hierarchy": r"\b(manager|managers|reports? to|reporting|direct reports?|designation|team members?|subordinates?)\b",
    "odc": r"\b(onsite|offshore|working days|lob|delivery manager|dm name|project location)\b",
    "meeting": r"\b(decisions?|tasks?|deadlines?|owner|recording|summar(?:y|ize|ise))\b",
}


def extract_employee_ids(text: str) -> list[str]:
    seen = []
    for m in ID_RE.findall(text or ""):
        if m not in seen:
            seen.append(m)
    return seen


def _match(patterns: dict, q: str) -> set[str]:
    return {m for m, p in patterns.items() if re.search(p, q, re.I)}


ROUTER_PROMPT = """Decide which data modules are needed to answer the question.

Modules:
- attendance: daily attendance per employee (present, absent, WFH, leave, check-in/out times, attendance percentages)
- hierarchy: organization chart (employee names, designation, manager, who reports to whom, location, joining date, email)
- odc: ODC tracker (ODC working days, ODC roster, project, PM, LOB, delivery manager)
- meeting: meeting notes (summaries, transcripts, decisions, action items / tasks, owners, deadlines)

Rules:
- Select every module needed. Questions that combine topics need several modules.
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
        mods = json.loads(match.group(0)).get("modules", [])
    except (ValueError, AttributeError):
        return None
    chosen = {m for m in mods if m in VALID}
    return chosen or None


def route_question(question: str, employee_ids: list[str] | None = None) -> list[str]:
    ids = employee_ids if employee_ids is not None else extract_employee_ids(question)
    strong = _match(STRONG, question)
    broad = _match(BROAD, question)

    if ids:
        # An employee ID is a deterministic lookup: no LLM call needed.
        chosen = strong | broad or {"attendance", "hierarchy", "odc"}
    else:
        llm = _llm_modules(question)
        chosen = set(strong) | (llm if llm is not None else broad)
        if not chosen and re.search(r"\b(employees?|staff|people|everyone)\b", question, re.I):
            chosen = {"attendance", "hierarchy", "odc"}

    return [m for m in VALID if m in chosen]