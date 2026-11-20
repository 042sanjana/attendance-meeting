 
import logging
 
from langgraph.graph import StateGraph, START, END
 
from app.chatbot.graph.state import ChatState
from app.chatbot.graph.supervisor import supervisor_node
 
from app.chatbot.agents.attendance_agent import (
    run_attendance_agent,
    run_odc_agent,
)
 
from app.chatbot.agents.hierarchy_agent import (
    run_hierarchy_agent,
)
 
from app.chatbot.agents.meeting_agent import (
    run_meeting_agent,
)
 
from app.chatbot.agents.rag_agent import (
    run_rag_agent,
)
 
from app.chatbot.agents.analyst_agent import (
    run_analyst_agent,
)
 
 
logger = logging.getLogger(__name__)
 
 
# --------------------------------------------------
# SAFE AGENT EXECUTION
# --------------------------------------------------
 
def safe_agent(agent_function, question, module):
 
    try:
        return agent_function(question)
 
    except Exception as exc:
 
        logger.exception(
            "%s agent failed",
            module,
        )
 
        return {
            "module": module,
            "error": str(exc),
            "data": {
                "columns": [],
                "rows": [],
                "row_count": 0,
            },
        }
 
 
# --------------------------------------------------
# ATTENDANCE NODE
# --------------------------------------------------
 
def attendance_node(state: ChatState):
 
    if "attendance" not in state.get(
        "selected_modules", []
    ):
        return {}
 
    result = safe_agent(
        run_attendance_agent,
        state["question"],
        "attendance",
    )
 
    return {
        "attendance_result": result,
    }
 
 
# --------------------------------------------------
# HIERARCHY NODE
# --------------------------------------------------
 
def hierarchy_node(state: ChatState):
 
    if "hierarchy" not in state.get(
        "selected_modules", []
    ):
        return {}
 
    result = safe_agent(
        run_hierarchy_agent,
        state["question"],
        "hierarchy",
    )
 
    return {
        "hierarchy_result": result,
    }
 
 
# --------------------------------------------------
# ODC NODE
# --------------------------------------------------
 
def odc_node(state: ChatState):
 
    if "odc" not in state.get(
        "selected_modules", []
    ):
        return {}
 
    result = safe_agent(
        run_odc_agent,
        state["question"],
        "odc",
    )
 
    return {
        "odc_result": result,
    }
 
 
# --------------------------------------------------
# MEETING NODE
# --------------------------------------------------
 
def meeting_node(state: ChatState):
 
    if "meeting" not in state.get(
        "selected_modules", []
    ):
        return {}
 
    meeting_result = safe_agent(
        run_meeting_agent,
        state["question"],
        "meeting",
    )
 
    rag_result = ""
 
    try:
        rag_result = run_rag_agent(
            state["question"]
        )
 
    except Exception:
        logger.exception(
            "Meeting RAG search failed"
        )
 
    return {
        "meeting_result": meeting_result,
        "rag_result": rag_result,
    }
 
 
# --------------------------------------------------
# ANALYST NODE
# --------------------------------------------------
 
def analyst_node(state: ChatState):
 
    evidence = {}
 
    result_keys = [
        "attendance_result",
        "hierarchy_result",
        "odc_result",
        "meeting_result",
    ]
 
    for key in result_keys:
 
        value = state.get(key)
 
        if value and not value.get("error"):
            evidence[key] = value
 
    if state.get("rag_result"):
        evidence["meeting_transcript_search"] = (
            state["rag_result"]
        )
 
    if not evidence:
 
        errors = [
            state.get(key, {}).get("error")
            for key in result_keys
            if state.get(key, {}).get("error")
        ]
 
        return {
            "answer": (
                "I could not retrieve the requested "
                "workforce records. Please check the "
                "database connection and backend logs. "
                + "; ".join(errors)
            )
        }
 
    try:
 
        answer = run_analyst_agent(
            state["question"],
            evidence,
        )
 
        return {
            "answer": answer,
        }
 
    except Exception as exc:
 
        logger.exception(
            "Workforce analyst failed"
        )
 
        return {
            "answer": (
                "Records were retrieved, but the "
                f"analysis failed: {exc}"
            )
        }
 
 
# --------------------------------------------------
# BUILD LANGGRAPH WORKFLOW
# --------------------------------------------------
 
def build_workflow():
 
    graph = StateGraph(ChatState)
 
    graph.add_node(
        "supervisor",
        supervisor_node,
    )
 
    graph.add_node(
        "attendance",
        attendance_node,
    )
 
    graph.add_node(
        "hierarchy",
        hierarchy_node,
    )
 
    graph.add_node(
        "odc",
        odc_node,
    )
 
    graph.add_node(
        "meeting",
        meeting_node,
    )
 
    graph.add_node(
        "analyst",
        analyst_node,
    )
 
    graph.add_edge(
        START,
        "supervisor",
    )
 
    graph.add_edge(
        "supervisor",
        "attendance",
    )
 
    graph.add_edge(
        "attendance",
        "hierarchy",
    )
 
    graph.add_edge(
        "hierarchy",
        "odc",
    )
 
    graph.add_edge(
        "odc",
        "meeting",
    )
 
    graph.add_edge(
        "meeting",
        "analyst",
    )
 
    graph.add_edge(
        "analyst",
        END,
    )
 
    return graph.compile()
 