from collections import defaultdict, deque


_history = defaultdict(lambda: deque(maxlen=10))
_entities = defaultdict(set)


def get_history(session_id: str):
    return list(_history[session_id])


def add_message(session_id: str, user_message: str, assistant_message: str):
    _history[session_id].append({
        "user": user_message,
        "assistant": assistant_message,
    })


def get_entities(session_id: str) -> set[str]:
    return set(_entities[session_id])


def remember(session_id: str, message: str, tables=None):
    """Remember lightweight employee/ID context for follow-up questions."""
    from app.chatbot.tools.schema_discovery import find_employee_ids_in_text
    for employee_id in find_employee_ids_in_text(message):
        _entities[session_id].add(employee_id)


def contextualize_question(question: str, history: list, entities=None) -> str:
    if not history:
        return question

    follow_up_starters = (
        "what about",
        "and ",
        "also ",
        "how about",
        "compare that",
        "why",
        "show me those",
        "which of them",
    )

    if question.strip().lower().startswith(follow_up_starters):
        previous_question = history[-1]["user"]
        return f"Previous question: {previous_question}\nCurrent follow-up: {question}"

    return question
