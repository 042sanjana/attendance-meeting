import logging
import os
import re

from app.chatbot.graph.workflow import build_workflow
from app.chatbot.services.memory_service import (
    add_message,
    contextualize_question,
    get_entities,
    get_history,
    remember,
)

log = logging.getLogger(__name__)
_workflow = None

GREETINGS = {
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "what can you do", "help",
}
GREETING_REPLY = (
    "Hello! I can answer questions across **Attendance**, **Organization Hierarchy**, "
    "**Meeting Notes** and the **ODC Tracker**, including questions that combine them. "
    "I can also summarize a live meeting recording."
)
UNCLEAR_REPLY = (
    "I could not tell which data your question is about. Please mention attendance, "
    "an employee or manager, ODC days, or a meeting, and I will look it up."
)
FAILURE_REPLY = (
    "I could not complete that analysis because a data source or the local AI model "
    "was unavailable. Please check that the backend and Ollama are running, then try again."
)


def get_workflow():
    global _workflow
    if _workflow is None:
        _workflow = build_workflow()
    return _workflow


def _reply(session_id, message, answer, sources=None, tables=None):
    add_message(session_id, message, answer)
    remember(session_id, message, tables)
    return {
        "answer": answer,
        "session_id": session_id,
        "sources": sources or [],
        "tables": tables or [],
    }


def chat(message: str, session_id: str) -> dict:
    history = get_history(session_id)
    question = contextualize_question(message, history, get_entities(session_id))

    if re.sub(r"[^\w\s]", "", message).strip().lower() in GREETINGS:
        return _reply(session_id, message, GREETING_REPLY)

    try:
        result = get_workflow().invoke({
            "question": question,
            "raw_question": message,
            "session_id": session_id,
        })
    except Exception as exc:
        log.exception("Chat workflow failed")
        reply = FAILURE_REPLY
        if os.getenv("CHATBOT_DEBUG", "").lower() in ("1", "true", "yes"):
            reply += f"\n\nDebug detail: {type(exc).__name__}: {exc}"
        return _reply(session_id, message, reply)

    if not result.get("selected_modules"):
        return _reply(session_id, message, UNCLEAR_REPLY)

    return _reply(
        session_id,
        message,
        result.get("answer") or "I could not generate an answer from the available records.",
        result.get("sources"),
        result.get("tables"),
    )