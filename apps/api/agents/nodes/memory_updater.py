"""
Memory updater node: writes assessment results to long-term memory (knowledge_memories).
"""
from api.agents.state import InterviewState
from api.services import memory_service


async def memory_updater_node(state: InterviewState) -> dict:
    memory_updates = state.get("memory_updates", [])
    if not memory_updates:
        return {}

    memory_service.apply_memory_updates(
        memory_updates,
        interview_id=state.get("session_id", ""),
    )
    return {}
