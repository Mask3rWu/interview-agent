"""
LangGraph interview state machine.
Builds a StateGraph with nodes: initializer → question_router → interviewer / assessment → memory_updater.
"""
from langgraph.graph import StateGraph, END

from app.agents.state import InterviewState
from app.agents.nodes.initializer import initializer_node
from app.agents.nodes.question_router import question_router_node
from app.agents.nodes.interviewer import interviewer_node
from app.agents.nodes.assessment import assessment_node
from app.agents.nodes.memory_updater import memory_updater_node


def build_interview_graph() -> StateGraph:
    graph = StateGraph(InterviewState)

    graph.add_node("initializer", initializer_node)
    graph.add_node("question_router", question_router_node)
    graph.add_node("interviewer", interviewer_node)
    graph.add_node("assessment", assessment_node)
    graph.add_node("memory_updater", memory_updater_node)

    graph.set_entry_point("initializer")
    graph.add_edge("initializer", "question_router")

    graph.add_conditional_edges(
        "question_router",
        _route_after_router,
        {
            "interviewer": "interviewer",
            "assessment": "assessment",
        },
    )

    graph.add_edge("interviewer", END)
    graph.add_edge("assessment", "memory_updater")
    graph.add_edge("memory_updater", END)

    return graph.compile()


def _route_after_router(state: InterviewState) -> str:
    action = state.get("action", "initial_question")
    if action == "assess":
        return "assessment"
    return "interviewer"
