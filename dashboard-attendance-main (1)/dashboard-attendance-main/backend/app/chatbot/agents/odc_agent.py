 
from app.chatbot.agents.attendance_agent import (
    get_llm,
    extract_sql,
)
from app.chatbot.tools.schema_discovery import get_module_schema
from app.chatbot.tools.attendance_tools import query_odc
 
 
def run_odc_agent(question: str) -> dict:
 
    q = question.lower().strip()
 
    # Exact dashboard calculation for an unfiltered total.
    asks_total = (
        "total" in q
        and ("odc" in q or "working days" in q)
    )
 
    has_date_filter = any(
        word in q
        for word in [
            "january", "february", "march", "april",
            "may", "june", "july", "august",
            "september", "october", "november",
            "december", "2024", "2025", "2026",
            "this month", "last month", "this year",
        ]
    )
 
    if asks_total and not has_date_filter:
 
        sql = """
        SELECT
            (
                SELECT COUNT(*)
                FROM (
                    SELECT emp_id, date(log_date)
                    FROM odc_logs
                    WHERE log_date IS NOT NULL
                      AND TRIM(COALESCE(emp_id, '')) <> ''
                    GROUP BY emp_id, date(log_date)
                )
            ) AS total_odc_working_days,
 
            (
                SELECT COUNT(*)
                FROM (
                    SELECT emp_id
                    FROM odc_employees
                    WHERE TRIM(COALESCE(emp_id, '')) <> ''
 
                    UNION
 
                    SELECT emp_id
                    FROM odc_logs
                    WHERE log_date IS NOT NULL
                      AND TRIM(COALESCE(emp_id, '')) <> ''
                )
            ) AS total_employees
        """
 
        data = query_odc(sql)
 
        if data["rows"]:
            row = data["rows"][0]
 
            total_days = int(
                row["total_odc_working_days"] or 0
            )
 
            total_employees = int(
                row["total_employees"] or 0
            )
 
            average = (
                round(total_days / total_employees, 1)
                if total_employees else 0
            )
 
            row["average_working_days"] = average
 
            data["columns"].append(
                "average_working_days"
            )
 
        return {
            "module": "odc",
            "calculation": "dashboard_matching",
            "sql": sql,
            "data": data,
        }
 
    # For other ODC questions, use the actual database schema.
    schema = get_module_schema("odc")
 
    prompt = f"""
You are an expert SQLite ODC analytics assistant.
 
DATABASE SCHEMA:
{schema}
 
USER QUESTION:
{question}
 
STRICT RULES:
 
1. Return only one SQLite SELECT query.
2. Use only actual tables and columns.
3. Never invent dates.
4. Never assume January 2023 or any default year.
5. If the user does not specify a date range,
   include all available dates.
6. ODC working days mean UNIQUE employee-date combinations.
7. Use GROUP BY emp_id, date(log_date) to avoid duplicate days.
8. Do not count multiple LOB or DM records on one day twice.
9. Use odc_employees for employee roster information.
10. Use odc_logs for actual ODC working-day records.
11. Use LEFT JOIN when employees with zero working days
    must also be included.
12. For employee lists, include employee ID and name.
13. Never modify the database.
14. Return SQL only.
 
IMPORTANT:
The dashboard calculates total working days by summing
unique working days across employees, not by counting
only distinct calendar dates.
"""
 
    response = get_llm().invoke(prompt)
    sql = extract_sql(response.content)
 
    data = query_odc(sql)
 
    return {
        "module": "odc",
        "sql": sql,
        "data": data,
    }
 