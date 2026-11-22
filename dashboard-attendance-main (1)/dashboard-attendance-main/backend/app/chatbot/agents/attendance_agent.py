import re
 
from app.chatbot.agents.sql_agent import run_module_agent


def find_employee_id(question: str):
    """Compatibility helper; routing now discovers actual database IDs."""
    from app.chatbot.tools.schema_discovery import find_employee_ids_in_text
    ids = find_employee_ids_in_text(question)
    return ids[0] if ids else None


def run_attendance_agent(question: str, employee_ids=None) -> dict:
    return run_module_agent("attendance", question, employee_ids)


def run_odc_agent(question: str, employee_ids=None) -> dict:
    return run_module_agent("odc", question, employee_ids)
