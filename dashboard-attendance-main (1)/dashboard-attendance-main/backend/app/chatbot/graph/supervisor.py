from app.chatbot.graph.routing import extract_employee_ids, route_question


def supervisor_node(state):
    question = state["question"]
    employee_ids = extract_employee_ids(question)
    modules = route_question(question, employee_ids)

    return {
        "selected_modules": modules,
        "employee_ids": employee_ids,
        "sources": [],
    }
