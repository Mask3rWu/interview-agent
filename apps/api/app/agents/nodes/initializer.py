"""
Initializer node: loads session data, profiles, materials, and long-term memory.
On first run, selects initial topic and sets action.
On subsequent runs (messages already present), acts as a pass-through.
"""
from app.agents.state import InterviewState
from app.services import resume_service, job_service, material_service, memory_service
from app.db import repositories

TOPIC_POOL = [
    "技术栈与项目经验",
    "系统设计",
    "数据库与存储",
    "编程基础与算法",
    "架构与设计模式",
    "团队协作与流程",
]


async def initializer_node(state: InterviewState) -> dict:
    session_id = state.get("session_id", "")

    # If already initialized (has messages), skip
    if state.get("messages") and len(state["messages"]) > 0:
        return {}

    # Load session from DB
    session = repositories.get("interviews", session_id)
    if session is None:
        return {"action": "assess", "assessment": {"error": "Session not found"}}

    resume = None
    job = None
    materials = []

    rid = session.get("resume_profile_id")
    if rid:
        r = resume_service.get_resume(rid)
        if r:
            resume = r.model_dump()

    jid = session.get("job_profile_id")
    if jid:
        j = job_service.get_job(jid)
        if j:
            job = j.model_dump()

    for mid in session.get("selected_material_ids", []):
        m = material_service.get_material(mid)
        if m:
            materials.append(m.model_dump())

    weakness_memory = memory_service.list_weakness_memories(limit=5)

    first_topic = _pick_initial_topic(job, resume, weakness_memory)

    return {
        "resume_profile": resume,
        "job_profile": job,
        "selected_material_ids": session.get("selected_material_ids", []),
        "retrieved_context": [],
        "weakness_memory": weakness_memory,
        "current_topic": first_topic,
        "covered_topics": [],
        "action": "initial_question",
        "follow_up_count": 0,
        "unclear_count": 0,
        "current_round": session.get("current_round", 0),
        "max_rounds": session.get("max_rounds", 8),
        "assessment": None,
        "assessment_status": "pending",
        "assessment_error": "",
        "memory_updates": [],
        "router_source": "",
    }


def _pick_initial_topic(job: dict | None, resume: dict | None, weakness_memory: list[dict]) -> str:
    if job:
        skills = job.get("must_have_skills_json") or []
        if skills:
            return str(skills[0])[:80]
        if job.get("domain"):
            return f"{job.get('domain')}岗位核心要求"
        return f"{job.get('name', '')}岗位核心要求"

    if resume:
        questions = resume.get("potential_questions_json") or []
        if questions:
            return str(questions[0])[:80]
        highlights = resume.get("project_highlights") or []
        if highlights:
            return str(highlights[0])[:80]

    if weakness_memory:
        return weakness_memory[0].get("topic", TOPIC_POOL[0])

    return TOPIC_POOL[0]
