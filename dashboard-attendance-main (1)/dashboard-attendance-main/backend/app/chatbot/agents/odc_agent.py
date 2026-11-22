from app.chatbot.agents.sql_agent import run_module_agent


def run_odc_agent(question: str, employee_ids=None) -> dict:
    return run_module_agent("odc", question, employee_ids)
