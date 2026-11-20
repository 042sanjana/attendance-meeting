 
import re
 
 
def route_question(question: str) -> list[str]:
 
    q = question.lower().strip()
 
    # --------------------------------------------------
    # 1. Direct employee ID questions.
    # --------------------------------------------------
 
    employee_id_pattern = (
        r"\bemp(?:loyee)?\s*id\s*[:#]?\s*[a-z0-9_-]+"
    )
 
    if re.search(employee_id_pattern, q):
        return ["attendance"]
 
    # --------------------------------------------------
    # 2. Cross-module questions.
    # --------------------------------------------------
 
    cross_module_words = [
        "compare",
        "across modules",
        "overall",
        "organization-wide",
        "company-wide",
        "all departments",
        "all modules",
        "entire workforce",
        "workforce summary",
    ]
 
    if any(word in q for word in cross_module_words):
        return [
            "attendance",
            "hierarchy",
            "odc",
            "meeting",
        ]
 
    # --------------------------------------------------
    # 3. Module keywords.
    # --------------------------------------------------
 
    attendance_words = [
        "attendance",
        "present",
        "absent",
        "wfh",
        "work from home",
        "leave",
        "weekly holiday",
        "public holiday",
        "checkin",
        "check-in",
        "check in",
        "check out",
        "checkout",
        "late",
        "working hours",
        "hours worked",
    ]
 
    hierarchy_words = [
        "manager",
        "reporting",
        "reports to",
        "hierarchy",
        "designation",
        "department",
        "employee structure",
        "team members",
        "direct report",
        "organization chart",
        "organization hierarchy",
    ]
 
    odc_words = [
        "odc",
        "onsite",
        "offshore",
        "odc working days",
        "odc days",
        "project location",
        "lob",
        "delivery manager",
        "dm name",
    ]
 
    meeting_words = [
        "meeting",
        "transcript",
        "minutes",
        "action item",
        "action items",
        "decision",
        "decisions",
        "meeting notes",
        "task owner",
        "deadline",
        "recording",
        "pending task",
        "pending tasks",
        "completed task",
        "completed tasks",
    ]
 
    modules = set()
 
    if any(word in q for word in attendance_words):
        modules.add("attendance")
 
    if any(word in q for word in hierarchy_words):
        modules.add("hierarchy")
 
    if any(word in q for word in odc_words):
        modules.add("odc")
 
    if any(word in q for word in meeting_words):
        modules.add("meeting")
 
    # --------------------------------------------------
    # 4. Employee-related questions.
    # --------------------------------------------------
 
    if "employee" in q and not modules:
        modules.update([
            "attendance",
            "hierarchy",
            "odc",
        ])
 
    # --------------------------------------------------
    # 5. General workforce questions.
    # --------------------------------------------------
 
    if not modules:
        modules.update([
            "attendance",
            "hierarchy",
            "odc",
            "meeting",
        ])
 
    return sorted(modules)
 