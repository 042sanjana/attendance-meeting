 
import json
 
from app.chatbot.agents.attendance_agent import get_llm
 
 
def clean_evidence(value):
 
    if isinstance(value, dict):
        return {
            key: clean_evidence(item)
            for key, item in value.items()
            if key.lower() not in {
                "sql",
                "query",
                "prompt",
            }
        }
 
    if isinstance(value, list):
        return [
            clean_evidence(item)
            for item in value
        ]
 
    return value
 
 
def run_analyst_agent(question: str, evidence: dict) -> str:
 
    # --------------------------------------------------
    # 1. Direct employee lookup.
    # No LLM required.
    # --------------------------------------------------
 
    attendance = evidence.get(
        "attendance_result",
        {},
    )
 
    if attendance.get("lookup_type") == "employee_by_id":
 
        rows = attendance.get(
            "data", {}
        ).get("rows", [])
 
        employee_id = attendance.get(
            "employee_id",
            "Unknown",
        )
 
        if not rows:
            return (
                f"No employee found with ID {employee_id} "
                "in the attendance database."
            )
 
        employee = rows[0]
 
        return (
            "**Employee Details**\n\n"
            f"Employee ID: {employee.get('emp_id', 'N/A')}\n\n"
            f"Employee Name: {employee.get('name', 'N/A')}"
        )
        
        
        
       
 
 
    # --------------------------------------------------
    # 2. Normal workforce analysis.
    # --------------------------------------------------
 
    actual_data = clean_evidence(evidence)
 
    evidence_text = json.dumps(
        actual_data,
        default=str,
        ensure_ascii=False,
    )[:18000]
 
    prompt = f"""
You are a professional Workforce Management Data Analyst.
 
USER QUESTION:
{question}
 
ACTUAL DATABASE RESULTS:
{evidence_text}
 
STRICT RULES:
 
1. Answer using only the supplied database results.
2. Never invent employee names or IDs.
3. Never invent dates or attendance statuses.
4. Never assume missing records.
5. Use actual retrieved counts.
6. Do not confuse attendance records with ODC records.
7. Do not count duplicate employee records as different employees.
8. For employee questions, show names and IDs when available.
9. For pending tasks, use actual task status.
10. If no matching records exist, say so clearly.
11. If a database module failed, do not pretend it was searched.
12. Do not display SQL queries.
13. Use simple language and readable formatting.
14. For totals and statistics, trust the supplied SQL results.
15. If the evidence is incomplete, explain the limitation.
 
Return the final answer only.
"""
 
    response = get_llm().invoke(prompt)
 
    return response.content.strip()
 