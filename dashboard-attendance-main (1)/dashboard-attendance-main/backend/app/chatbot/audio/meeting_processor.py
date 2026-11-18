
import json
import re

from app.chatbot.agents.attendance_agent import get_llm


def extract_json(text: str):
    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL,
    )

    if not match:
        raise ValueError("Gemma did not return valid JSON.")

    return json.loads(match.group(0))


def process_transcript(transcript: str) -> dict:
    if not transcript or not transcript.strip():
        raise ValueError("Transcript is empty.")

    prompt = f"""
Analyze this meeting transcript.

TRANSCRIPT:
{transcript[:12000]}

Return valid JSON with this exact structure:
{{
  "summary": "short meeting summary",
  "decisions": ["decision 1"],
  "tasks": [
    {{
      "owner": "person name or Unknown",
      "task": "action description",
      "deadline_text": "deadline mentioned or Not specified",
      "priority": "High, Medium, Low, or Not specified"
    }}
  ]
}}

Rules:
- Do not invent people, decisions, deadlines or tasks.
- Use Unknown when the owner is not clear.
- Use Not specified when no deadline is stated.
- Return JSON only.
"""

    response = get_llm().invoke(prompt)
    result = extract_json(response.content)

    return result
