from datetime import datetime
from pydantic import BaseModel, Field


class InterviewCreate(BaseModel):
    resume_profile_id: str | None = Field(default=None, description="简历画像ID")
    job_profile_id: str | None = Field(default=None, description="岗位画像ID")
    material_ids: list[str] = Field(default_factory=list, description="选择的资料ID列表")
    use_all_materials: bool = Field(default=False, description="是否使用全部资料")
    max_rounds: int = Field(default=8, ge=2, le=20, description="最大轮次")


class InterviewSession(BaseModel):
    id: str
    resume_profile_id: str | None = None
    job_profile_id: str | None = None
    selected_material_ids: list[str] = Field(default_factory=list)
    status: str = "active"
    messages: list[dict] = Field(default_factory=list)
    current_topic: str | None = None
    covered_topics: list[str] = Field(default_factory=list)
    follow_up_count: int = 0
    unclear_count: int = 0
    current_round: int = 0
    max_rounds: int = 8
    assessment: dict | None = None
    assessment_status: str = "pending"
    assessment_error: str = ""
    memory_updates: list[dict] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class AnswerRequest(BaseModel):
    answer: str = Field(description="用户回答文本")


class InterviewEvent(BaseModel):
    event: str  # token, message_end, assessment, error, first_question
    data: str | dict | None = None
