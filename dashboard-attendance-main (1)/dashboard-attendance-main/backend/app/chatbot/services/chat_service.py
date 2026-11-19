from app.chatbot.graph.workflow import build_workflow

from app.chatbot.services.memory_service import (
    get_history,
    add_message,
    contextualize_question,
)


_workflow = None


def get_workflow():
    global _workflow

    if _workflow is None:
        _workflow = build_workflow()

    return _workflow


def chat(message: str, session_id: str) -> dict:
    history = get_history(session_id)

    question = contextualize_question(
        message,
        history,
    )

    greeting = message.strip().lower()
    if greeting in {"hi", "hello", "hey", "good morning", "good afternoon", "good evening", "what can you do", "help"}:
        answer = (
            "Hello! I can answer questions across Attendance, Organization Hierarchy, "
            "AI Meeting Notes and ODC Tracker. I can also summarize a live meeting recording."
        )
        add_message(session_id, message, answer)
        return {"answer": answer, "session_id": session_id, "sources": []}

    try:
        result = get_workflow().invoke({
            "question": question,
            "session_id": session_id,
        })
    except Exception as exc:
        import logging 
        logging.exception("workflow chatbot failed")
        answer = (
            f"Unable to complete the analysis."f"Please check the connected database or Ollama service."
            f"Error:{str}"
        )
        add_message(session_id, message, answer)
        return {"answer": answer, "session_id": session_id, "sources": []}

    answer = result.get(
        "answer",
        "I could not generate an answer from the available records."
    )

    add_message(
        session_id,
        message,
        answer,
    )

    return {
        "answer": answer,
        "session_id": session_id,
        "sources": [
            {
                "module": module,
                "description": (
                    f"Retrieved records from {module}."
                ),
            }
            for module in (
                "attendance_result",
                "hierarchy_result",
                "odc_result",
                "meeting_result",
            )
            if result.get(module)
        ],
    }
