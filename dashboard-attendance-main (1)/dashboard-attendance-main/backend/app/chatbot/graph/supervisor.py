from app.chatbot.graph.routing import extract_employee_ids, route_question
from app.chatbot.tools.schema_discovery import find_employee_names_in_text


def supervisor_node(state):
    question = state["question"]
    employee_ids = extract_employee_ids(question)
    employee_names = find_employee_names_in_text(question)
    modules = route_question(question, employee_ids)

    if employee_names:
        q = question.lower()
        names_modules = {"attendance", "hierarchy", "odc"}
        if "odc" in q:
            names_modules = {"odc"}
        elif "attendance" in q or any(word in q for word in ("present", "absent", "wfh")):
            names_modules = {"attendance"}
        elif any(word in q for word in ("manager", "designation", "location", "employee details", "employee id", "emp id")):
            names_modules = {"hierarchy"}
        modules = [module for module in ("attendance", "hierarchy", "odc", "meeting") if module in names_modules]

    return {
        "selected_modules": modules,
        "employee_ids": employee_ids,
        "employee_names": employee_names,
        "sources": [],
    }
