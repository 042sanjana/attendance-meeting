import re
import dateparser

from datetime import datetime

HIGH_PRIORITY_WORDS = [
"urgent",
"urgently",
"asap",
"critical",
"immediately",
"today",
"high priority",
"top priority",
"highest priority",
"priority one",
"priority 1",
"blocker",
"blocking",
"must",
"must complete",
"must finish",
"must deliver",
"need immediately",
"needs immediate attention",
"time sensitive",
"deadline today",
"before end of day",
"eod",
"end of day",
"production issue",
"hotfix",
"escalated",
"escalation",
"customer issue",
"client issue",
"critical bug",
"major bug",
"security issue",
"security fix",
"showstopper",
"high impact",
"cannot wait"
]

MEDIUM_PRIORITY_WORDS = [
"important",
"soon",
"this week",
"by this week",
"medium priority",
"priority two",
"priority 2",
"should",
"should complete",
"should finish",
"please complete",
"please finish",
"follow up",
"follow-up",
"review",
"review needed",
"needs review",
"required",
"necessary",
"expected",
"recommended",
"planned",
"scheduled",
"upcoming release",
"prepare",
"coordinate",
"check",
"verify",
"validate",
"testing required",
"deployment preparation"
]

LOW_PRIORITY_WORDS = [
"whenever possible",
"low priority",
"nice to have",
"optional",
"future",
"later",
"eventually",
"backlog",
"enhancement",
"improvement",
"consider",
"explore",
"investigate",
"research",
"look into",
"if time permits",
"someday",
"not urgent"
]

from datetime import datetime

EMPLOYEE_ID_RE = re.compile(
    r"\b(?:EMPLOYEE\s*(?:ID|NUMBER)?\s*[:#]?\s*)?"
    r"((?:EMP|E)[-_]?\d{2,}|ABC\d{2,}|[A-Z]{2,}\d{2,})\b",
    re.I,
)

DEADLINE_RE = re.compile(
    r"(?:by|before|within|due on|deadline(?:\s+(?:is|:))?)\s+([^.!?]+)",
    re.I,
)

PRIORITY_RE = re.compile(
    r"(?:high|medium|low)[-\s]+priority|priority\s*[:=-]?\s*(high|medium|low)",
    re.I,
)


def extract_employee_id(sentence: str) -> str | None:
    match = EMPLOYEE_ID_RE.search(sentence)
    if not match:
        return None
    return match.group(1).upper().replace(" ", "")


def extract_deadline(sentence: str) -> tuple[str | None, str | None]:
    match = DEADLINE_RE.search(sentence)
    if not match:
        return None, None

    deadline_text = match.group(1).strip()
    parsed = dateparser.parse(deadline_text, settings={"PREFER_DATES_FROM": "future"})
    deadline_date = parsed.strftime("%Y-%m-%d") if parsed else None
    return deadline_text, deadline_date


def extract_priority(sentence: str) -> str:
    match = PRIORITY_RE.search(sentence)
    if not match:
        return "Not specified"
    value = match.group(0).lower()
    if "high" in value:
        return "High"
    if "medium" in value:
        return "Medium"
    if "low" in value:
        return "Low"
    return "Not specified"


def extract_decisions(transcript: str) -> list[str]:
    decisions = []
    pattern = re.compile(
        r"(?:we\s+decided|decided\s+to|decision(?:\s+is)?|we\s+agreed|agreed\s+to|approved)\s+([^.!?]+)",
        re.I,
    )
    for match in pattern.finditer(transcript or ""):
        value = match.group(1).strip()
        if value and value not in decisions:
            decisions.append(value)
    return decisions


def detect_priority(deadline_date=None):

    if not deadline_date:
        return "Medium"

    try:

        deadline = datetime.strptime(
            deadline_date,
            "%Y-%m-%d"
        ).date()

        today = datetime.now().date()

        days_left = (
            deadline - today
        ).days

        if days_left < 0:
            return "Overdue"

        elif days_left <= 2:
            return "High"

        elif days_left <= 7:
            return "Medium"

        else:
            return "Low"

    except Exception:
        return "Medium"


def extract_tasks(transcript):

    tasks = []

    sentences = re.split(
        r"[.!?]",
        transcript
    )

    patterns = [

    r"([A-Z][a-z]+),\s*(.*?)\s+by\s+(.*?)(?:\.|$)",
    
    r"([A-Z][a-z]+),\s*(.*?)\s+before\s+(.*?)(?:\.|$)",

    r"([A-Z][a-z]+)\s+will\s+(.*?)\s+by\s+(.*?)(?:\.|$)",

    r"([A-Z][a-z]+)\s+should\s+(.*?)\s+by\s+(.*?)(?:\.|$)",

    r"([A-Z][a-z]+)\s+needs?\s+to\s+(.*?)\s+by\s+(.*?)(?:\.|$)",

    r"([A-Z][a-z]+)\s+must\s+(.*?)\s+by\s+(.*?)(?:\.|$)"
]
    

    seen = set()

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        for pattern in patterns:

            match = re.search(
                pattern,
                sentence,
                re.IGNORECASE
            )

            if not match:
                continue

            person, task, deadline = match.groups()

            task_key = (
                person.lower(),
                task.lower()
            )

            if task_key in seen:
                continue

            seen.add(task_key)

            parsed_date = dateparser.parse(
                deadline,
                settings={
                    "PREFER_DATES_FROM": "future"
                }
            )

            deadline_date = None

            if parsed_date:
                deadline_date = parsed_date.strftime(
                    "%Y-%m-%d"
                )

            priority = detect_priority(
                deadline_date
            )

            tasks.append(
                {
                    "owner": person.strip(),
                    "task": task.strip(),
                    "deadline_text": deadline.strip(),
                    "deadline_date": deadline_date,
                    "priority": priority,
                    "status": "Pending"
                }
            )

            break

    return tasks