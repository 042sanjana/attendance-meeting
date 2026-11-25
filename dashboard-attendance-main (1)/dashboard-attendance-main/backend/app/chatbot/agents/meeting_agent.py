from app.chatbot.agents.sql_agent import run_module_agent


def run_meeting_agent(question: str, employee_ids=None, employee_names=None) -> dict:
    return run_module_agent("meeting", question, employee_ids, employee_names)
