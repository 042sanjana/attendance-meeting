
from app.chatbot.tools.schema_discovery import get_module_schema
from app.chatbot.tools.sql_executor import execute_select


def get_hierarchy_schema():
    return get_module_schema("hierarchy")


def query_hierarchy(sql: str):
    return execute_select("hierarchy", sql)
