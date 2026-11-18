
from app.chatbot.graph.routing import route_question


def supervisor_node(state):
    modules = route_question(state["question"])

    return {
        "selected_modules": modules,
        "sources": [],
    }
