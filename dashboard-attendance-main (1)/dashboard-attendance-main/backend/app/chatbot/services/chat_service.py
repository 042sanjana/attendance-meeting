 
import logging
 
from app.chatbot.graph.workflow import build_workflow
 
from app.chatbot.services.memory_service import (
    get_history,
    add_message,
    contextualize_question,
)
 
 
logger = logging.getLogger(__name__)
 
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
 
    if greeting in {
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "what can you do",
        "help",
    }:
 
        answer = (
            "Hello! I can answer questions about "
            "Attendance, Organization Hierarchy, "
            "AI Meeting Notes and ODC Tracker. "
            "I use your uploaded workforce records "
            "to answer questions."
        )
 
        add_message(
            session_id,
            message,
            answer,
        )
 
        return {
            "answer": answer,
            "session_id": session_id,
            "sources": [],
        }
 
    try:
 
        result = get_workflow().invoke({
            "question": question,
            "session_id": session_id,
        })
 
        answer = result.get(
            "answer",
            "No answer could be generated from the available records.",
        )
 
        source_modules = {
            "attendance_result": "Attendance",
            "hierarchy_result": "Organization Hierarchy",
            "odc_result": "ODC Tracker",
            "meeting_result": "Meeting Notes",
        }
 
        sources = []
 
        for key, module in source_modules.items():
 
            value = result.get(key)
 
            if value and not value.get("error"):
 
                sources.append({
                    "module": module,
                    "description": (
                        f"Retrieved records from {module}."
                    ),
                })
 
        if result.get("rag_result"):
            sources.append({
                "module": "Meeting Transcript Search",
                "description": "Searched meeting transcripts.",
            })
 
        add_message(
            session_id,
            message,
            answer,
        )
 
        return {
            "answer": answer,
            "session_id": session_id,
            "sources": sources,
        }
 
    except Exception as exc:
 
        logger.exception(
            "Workforce chatbot request failed"
        )
 
        answer = (
            "The chatbot could not complete your request. "
            "Please check the backend logs and database connection. "
            f"Technical error: {exc}"
        )
 
        add_message(
            session_id,
            message,
            answer,
        )
 
        return {
            "answer": answer,
            "session_id": session_id,
            "sources": [],
        }
 