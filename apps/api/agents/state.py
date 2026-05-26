from typing import Annotated, TypedDict, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class InterviewState(TypedDict):
    session_id: str
    resume_profile: dict | None
    job_profile: dict | None
    selected_material_ids: list[str]
    retrieved_context: list[dict]
    weakness_memory: list[dict]

    messages: Annotated[list[BaseMessage], add_messages]
    current_topic: str | None
    covered_topics: list[str]
    action: Literal["initial_question", "follow_up", "switch_topic", "assess"]

    follow_up_count: int
    unclear_count: int
    current_round: int
    max_rounds: int

    assessment: dict | None
    assessment_status: Literal["pending", "success", "failed"]
    assessment_error: str
    memory_updates: list[dict]
    router_source: str
    report_path: str
