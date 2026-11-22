from app.chatbot.agents.sql_agent import run_module_agent


def run_hierarchy_agent(question: str, employee_ids=None) -> dict:
    return run_module_agent("hierarchy", question, employee_ids)
