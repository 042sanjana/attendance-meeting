import json
from app.chatbot.agents.attendance_agent import get_llm
 
 
def clean_evidence(value):
    """Keep actual records and remove internal SQL."""
    if isinstance(value, dict):
        return {
            key: clean_evidence(item)
            for key, item in value.items()
            if key.lower() not in {"sql", "query", "prompt"}
        }
    if isinstance(value, list):
        return [clean_evidence(item) for item in value]
    return value
 
 
def run_analyst_agent(question: str, evidence: dict) -> str:
    actual_data = clean_evidence(evidence)
 
    evidence_text = json.dumps(
        actual_data,
        default=str,
        ensure_ascii=False
    )[:14000]
 
    prompt = f"""
You are a professional Workforce Management Assistant.
 
USER QUESTION:
{question}
 
ACTUAL DATABASE RESULTS:
{evidence_text}
 
INSTRUCTIONS:
- Answer the question directly using actual database records.
- Return actual employee names, IDs, counts and dates.
- For employee ID questions, return the matching employee name.
- For summary questions, calculate using the supplied records.
- Never explain SQL or show database queries.
- Never invent missing information.
- If records are empty, clearly say no matching records were found.
- Use simple language, headings and readable tables where useful.
- Do not assume today's date. Use dates from the data.
- Do not confuse attendance records with ODC working days.
 
Give the final answer only.
"""
 
    response = get_llm().invoke(prompt)
    return response.content.strip()