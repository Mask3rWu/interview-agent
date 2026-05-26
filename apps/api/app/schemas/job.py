from datetime import datetime
from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    name: str = Field(description="岗位名称")
    company: str = Field(default="", description="公司名称")
    raw_text: str = Field(description="JD 原文")


class JobResponse(BaseModel):
    id: str
    name: str
    company: str = ""
    raw_text: str
    markdown_path: str = ""
    summary_json: dict = Field(default_factory=dict)
    must_have_skills_json: list = Field(default_factory=list)
    domain: str = ""
    level: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
