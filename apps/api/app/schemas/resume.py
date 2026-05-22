from datetime import datetime
from pydantic import BaseModel, Field


class ResumeCreate(BaseModel):
    name: str = Field(description="简历画像名称")
    raw_text: str = Field(description="简历原文")


class ResumeResponse(BaseModel):
    id: str
    name: str
    raw_text: str
    markdown_path: str = ""
    skills_json: dict = Field(default_factory=dict)
    potential_questions_json: list = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
