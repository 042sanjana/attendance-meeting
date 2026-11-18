
from typing import TypedDict, Any


class ChatState(TypedDict, total=False):
    question: str
    session_id: str
    selected_modules: list[str]
    attendance_result: dict[str, Any]
    hierarchy_result: dict[str, Any]
    meeting_result: dict[str, Any]
    odc_result: dict[str, Any]
    rag_result: str
    sources: list[dict[str, str]]
    answer: str
    error: str
