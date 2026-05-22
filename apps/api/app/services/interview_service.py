"""
Interview service using LangGraph for the interview state machine.
"""
import uuid
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage

from app.core import json_store
from app.schemas.interview import InterviewCreate, InterviewSession, InterviewEvent
from app.services import resume_service, job_service, material_service, memory_service
from app.agents.interview_graph import build_interview_graph


def create_session(data: InterviewCreate) -> InterviewSession:
    resume = None
    job = None
    materials = []

    if data.resume_profile_id:
        resume = resume_service.get_resume(data.resume_profile_id)
    if data.job_profile_id:
        job = job_service.get_job(data.job_profile_id)

    if data.use_all_materials:
        materials = material_service.list_materials()
    elif data.material_ids:
        for mid in data.material_ids:
            m = material_service.get_material(mid)
            if m:
                materials.append(m)

    session = {
        "resume_profile_id": data.resume_profile_id,
        "job_profile_id": data.job_profile_id,
        "selected_material_ids": (
            [m.id for m in materials] if data.use_all_materials else data.material_ids
        ),
        "status": "active",
        "messages": [],
        "current_topic": None,
        "covered_topics": [],
        "follow_up_count": 0,
        "unclear_count": 0,
        "current_round": 0,
        "max_rounds": data.max_rounds,
        "assessment": None,
        "assessment_status": "pending",
        "assessment_error": "",
        "memory_updates": [],
        "created_at": datetime.now().isoformat(),
    }

    saved = json_store.insert("interviews", session)
    return InterviewSession(**saved)


def list_sessions() -> list[dict]:
    """Return all interview sessions sorted by created_at descending (newest first).
    Returns lightweight summaries — full messages are excluded for performance.
    """
    records = json_store.list_all("interviews")
    summaries = []
    for r in records:
        summaries.append({
            "id": r.get("id"),
            "status": r.get("status"),
            "current_round": r.get("current_round", 0),
            "max_rounds": r.get("max_rounds", 0),
            "resume_profile_id": r.get("resume_profile_id"),
            "job_profile_id": r.get("job_profile_id"),
            "selected_material_ids": r.get("selected_material_ids", []),
            "total_score": r.get("assessment", {}).get("total_score") if r.get("assessment") else None,
            "assessment_status": r.get("assessment_status", "pending"),
            "assessment_error": r.get("assessment_error", ""),
            "memory_update_count": len(r.get("memory_updates", [])),
            "created_at": r.get("created_at"),
        })
    summaries.sort(key=lambda s: s.get("created_at") or "", reverse=True)
    return summaries


def get_session(session_id: str) -> InterviewSession | None:
    record = json_store.get("interviews", session_id)
    if record is None:
        return None
    return InterviewSession(**record)


def _save_session(session: InterviewSession) -> None:
    json_store.update("interviews", session.id, session.model_dump())


def _session_to_graph_state(session: InterviewSession) -> dict:
    """Convert InterviewSession to the dict format InterviewState expects."""
    messages = []
    for m in session.messages:
        if m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "interviewer":
            messages.append(AIMessage(content=m["content"]))

    return {
        "session_id": session.id,
        "resume_profile": None,
        "job_profile": None,
        "selected_material_ids": session.selected_material_ids,
        "retrieved_context": [],
        "weakness_memory": memory_service.list_weakness_memories(limit=5),
        "messages": messages,
        "current_topic": session.current_topic,
        "covered_topics": session.covered_topics,
        "action": "initial_question",
        "follow_up_count": session.follow_up_count,
        "unclear_count": getattr(session, "unclear_count", 0),
        "current_round": session.current_round,
        "max_rounds": session.max_rounds,
        "assessment": session.assessment,
        "assessment_status": getattr(session, "assessment_status", "pending"),
        "assessment_error": getattr(session, "assessment_error", ""),
        "memory_updates": getattr(session, "memory_updates", []),
    }


def _graph_state_to_session(state: dict, session: InterviewSession) -> None:
    """Update session fields from graph state output."""
    messages_raw = []
    for m in state.get("messages", []):
        if isinstance(m, HumanMessage):
            messages_raw.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            messages_raw.append({"role": "interviewer", "content": m.content})

    session.messages = messages_raw
    session.current_topic = state.get("current_topic", session.current_topic)
    session.covered_topics = state.get("covered_topics", session.covered_topics)
    session.follow_up_count = state.get("follow_up_count", session.follow_up_count)
    session.unclear_count = state.get("unclear_count", getattr(session, "unclear_count", 0))
    session.current_round = state.get("current_round", session.current_round)
    session.memory_updates = state.get("memory_updates", [])
    session.assessment = state.get("assessment", session.assessment)
    session.assessment_status = state.get("assessment_status", getattr(session, "assessment_status", "pending"))
    session.assessment_error = state.get("assessment_error", getattr(session, "assessment_error", ""))

    mem_updates = state.get("memory_updates", [])
    if mem_updates:
        session.memory_updates = mem_updates

    if state.get("assessment_status") == "success":
        session.status = "ended"
    elif state.get("assessment_status") == "failed":
        session.status = "ended"


async def generate_first_question(session: InterviewSession) -> InterviewEvent:
    graph = build_interview_graph()
    initial_state = _session_to_graph_state(session)

    result = await graph.ainvoke(initial_state)

    _graph_state_to_session(result, session)
    _save_session(session)

    # Extract last AI message as the first question
    last_msg = ""
    for m in reversed(session.messages):
        if m["role"] == "interviewer":
            last_msg = m["content"]
            break

    return InterviewEvent(event="first_question", data=last_msg)


async def submit_answer(session_id: str, answer: str) -> InterviewEvent:
    session = get_session(session_id)
    if session is None:
        return InterviewEvent(event="error", data="Session not found")
    if session.status != "active":
        return InterviewEvent(event="error", data="Session already ended")

    # Append user's answer as a message
    session.messages.append({"role": "user", "content": answer})

    graph = build_interview_graph()
    state = _session_to_graph_state(session)

    result = await graph.ainvoke(state)

    _graph_state_to_session(result, session)
    _save_session(session)

    # Check if assessment was generated
    if session.assessment or session.assessment_status == "failed":
        return InterviewEvent(event="assessment", data=session.assessment)

    # Extract last AI message as next question
    last_msg = ""
    for m in reversed(session.messages):
        if m["role"] == "interviewer":
            last_msg = m["content"]
            break

    return InterviewEvent(event="message_end", data=last_msg)


async def finish_interview(session_id: str) -> InterviewEvent:
    session = get_session(session_id)
    if session is None:
        return InterviewEvent(event="error", data="Session not found")
    if session.status != "active":
        return InterviewEvent(event="error", data="Session already ended")

    # Force assessment by setting action to assess
    session.messages.append({"role": "user", "content": "结束面试"})

    graph = build_interview_graph()
    state = _session_to_graph_state(session)
    # Force current_round >= max_rounds to trigger assessment
    state["current_round"] = session.max_rounds
    state["action"] = "assess"

    result = await graph.ainvoke(state)

    _graph_state_to_session(result, session)
    _save_session(session)

    return InterviewEvent(event="assessment", data=session.assessment)


async def reassess_interview(session_id: str) -> InterviewEvent:
    session = get_session(session_id)
    if session is None:
        return InterviewEvent(event="error", data="Session not found")

    graph = build_interview_graph()
    state = _session_to_graph_state(session)
    state["current_round"] = session.max_rounds
    state["action"] = "assess"

    result = await graph.ainvoke(state)
    _graph_state_to_session(result, session)
    _save_session(session)

    if session.assessment_status != "success":
        return InterviewEvent(event="error", data=session.assessment_error or "Assessment failed")

    if session.memory_updates:
        memory_service.apply_memory_updates(
            session.memory_updates,
            interview_id=session.id,
            tested_at=session.created_at,
        )
    return InterviewEvent(event="assessment", data=session.assessment)
