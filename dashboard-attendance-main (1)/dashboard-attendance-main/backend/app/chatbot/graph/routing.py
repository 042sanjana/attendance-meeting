
def route_question(question: str) -> list[str]:
    q = question.lower()
    modules = set()

    cross_module_words = [
        "compare", "across modules", "overall",
        "organization-wide", "company-wide",
        "all departments", "all modules",
    ]

    if any(word in q for word in cross_module_words):
        return ["attendance", "hierarchy", "odc", "meeting"]

    attendance_words = [
        "attendance", "present", "absent", "wfh",
        "leave", "half day", "checkin", "check-in",
        "check out", "late", "employee attendance",
    ]

    hierarchy_words = [
        "manager", "reporting", "reports to",
        "hierarchy", "designation", "department",
        "employee structure", "team members",
        "direct report", "organization chart",
    ]

    odc_words = [
        "odc", "onsite", "offshore", "working days",
        "odc days", "project location", "lob",
        "delivery manager", "dm name",
    ]

    meeting_words = [
        "meeting", "transcript", "minutes",
        "action item", "action items", "decision",
        "decisions", "meeting notes", "task owner",
        "deadline", "recording",
    ]

    if any(word in q for word in attendance_words):
        modules.add("attendance")

    if any(word in q for word in hierarchy_words):
        modules.add("hierarchy")

    if any(word in q for word in odc_words):
        modules.add("odc")

    if any(word in q for word in meeting_words):
        modules.add("meeting")

    # Employee questions can require cross-module information.
    if "employee" in q and not modules:
        modules.update(["attendance", "hierarchy", "odc"])

    # General meeting-related questions should search meeting records.
    if not modules:
        modules.update(["attendance", "hierarchy", "odc", "meeting"])
        

    return sorted(modules)
