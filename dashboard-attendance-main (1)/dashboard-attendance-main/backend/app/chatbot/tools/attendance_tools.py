
from app.chatbot.tools.schema_discovery import get_module_schema
from app.chatbot.tools.sql_executor import execute_select


def get_attendance_schema():
    return get_module_schema("attendance")


def query_attendance(sql: str):
    return execute_select("attendance", sql)


def query_odc(sql: str):
    return execute_select("odc", sql)
