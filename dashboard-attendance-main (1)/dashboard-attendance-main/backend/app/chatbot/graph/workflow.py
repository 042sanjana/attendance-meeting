
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
from app.chatbot.agents.rag_agent import run_rag_agent
from app.chatbot.agents.analyst_agent import run_analyst_agent


def attendance_node(state: ChatState):
    if "attendance" not in state.get("selected_modules", []):
        return {}

    result = run_attendance_agent(state["question"])

    return {
        "attendance_result": result,
    }


def hierarchy_node(state: ChatState):
    if "hierarchy" not in state.get("selected_modules", []):
        return {}

    result = run_hierarchy_agent(state["question"])

    return {
        "hierarchy_result": result,
    }


def odc_node(state: ChatState):
    if "odc" not in state.get("selected_modules", []):
        return {}

    result = run_odc_agent(state["question"])

    return {
        "odc_result": result,
    }


def meeting_node(state: ChatState):
    if "meeting" not in state.get("selected_modules", []):
        return {}

    result = run_meeting_agent(state["question"])

    rag_result = run_rag_agent(state["question"])

    return {
        "meeting_result": result,
        "rag_result": rag_result,
    }


def analyst_node(state: ChatState):
    evidence = {}

    for key in (
        "attendance_result",
        "hierarchy_result",
        "odc_result",
        "meeting_result",
    ):
        value = state.get(key)

        if value:
            evidence[key] = value

    if state.get("rag_result"):
        evidence["meeting_transcript_search"] = (
            state["rag_result"]
        )

    if not evidence:
        return {
            "answer": (
                "I could not retrieve relevant records from "
                "the connected modules."
            )
        }

    answer = run_analyst_agent(
        state["question"],
        evidence,
    )

    return {
        "answer": answer,
    }


def build_workflow():
    graph = StateGraph(ChatState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("attendance", attendance_node)
    graph.add_node("hierarchy", hierarchy_node)
    graph.add_node("odc", odc_node)
    graph.add_node("meeting", meeting_node)
    graph.add_node("analyst", analyst_node)

    graph.add_edge(START, "supervisor")
    graph.add_edge("supervisor", "attendance")
    graph.add_edge("attendance", "hierarchy")
    graph.add_edge("hierarchy", "odc")
    graph.add_edge("odc", "meeting")
    graph.add_edge("meeting", "analyst")
    graph.add_edge("analyst", END)

    return graph.compile()
