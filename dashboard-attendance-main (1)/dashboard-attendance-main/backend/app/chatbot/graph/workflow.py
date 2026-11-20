import logging

from langgraph.graph import END, START, StateGraph

from app.chatbot.agents.analyst_agent import build_final
from app.chatbot.agents.attendance_agent import run_attendance_agent
from app.chatbot.agents.odc_agent import run_odc_agent
from app.chatbot.agents.hierarchy_agent import run_hierarchy_agent
from app.chatbot.agents.meeting_agent import run_meeting_agent
from app.chatbot.agents.rag_agent import run_rag_agent
from app.chatbot.graph.state import ChatState
from app.chatbot.graph.supervisor import supervisor_node

log = logging.getLogger(__name__)

AGENTS = {
    "attendance": run_attendance_agent,
    "hierarchy": run_hierarchy_agent,
    "odc": run_odc_agent,
    "meeting": run_meeting_agent,
}


def retrieve_node(state: ChatState):
    """Runs only the selected agents, one after another (a local Ollama
    server handles one generation at a time, so parallelism would only
    risk timeouts)."""
    question = state["question"]
    ids = state.get("employee_ids") or []
    out: dict = {}

    for module in state.get("selected_modules") or []:
        try:
            out[f"{module}_result"] = AGENTS[module](question, ids)
        except Exception:
            log.exception("Agent %s crashed", module)
            out[f"{module}_result"] = {
                "module": module, "sql": None, "data": None, "error": "query_failed",
            }

    if "meeting" in (state.get("selected_modules") or []):
        try:
            out["rag_result"] = run_rag_agent(question)
        except Exception:
            log.exception("Transcript search failed")
            out["rag_result"] = ""
    return out


def analyst_node(state: ChatState):
    return build_final(state)


def build_workflow():
    graph = StateGraph(ChatState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("analyst", analyst_node)
    graph.add_edge(START, "supervisor")
    graph.add_edge("supervisor", "retrieve")
    graph.add_edge("retrieve", "analyst")
    graph.add_edge("analyst", END)
    return graph.compile()