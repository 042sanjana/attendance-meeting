
from collections import defaultdict, deque


_history = defaultdict(
    lambda: deque(maxlen=10)
)


def get_history(session_id: str):
    return list(_history[session_id])


def add_message(
    session_id: str,
    user_message: str,
    assistant_message: str,
):
    _history[session_id].append({
        "user": user_message,
        "assistant": assistant_message,
    })


def contextualize_question(
    question: str,
    history: list,
) -> str:
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

    q = question.strip().lower()

    if q.startswith(follow_up_starters):
        previous_question = history[-1]["user"]

        return (
            f"Previous question: {previous_question}\n"
            f"Current follow-up: {question}"
        )

    return question
