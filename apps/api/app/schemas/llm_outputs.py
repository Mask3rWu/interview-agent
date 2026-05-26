from pydantic import BaseModel, Field
from typing import Literal


class RouterDecision(BaseModel):
    action: Literal["follow_up", "switch_topic", "assess"] = Field(
        description="下一步动作：追问、切题或进入评估"
    )
    quality: Literal["excellent", "adequate", "vague", "wrong", "unknown"] = Field(
        default="adequate", description="用户上一轮回答质量"
    )
    next_topic: str | None = Field(default=None, description="切题时建议的新话题")
    reason: str = Field(default="", description="做出该决策的简短原因")


class AssessmentResult(BaseModel):
    total_score: int = Field(default=0, ge=0, le=100, description="总评分")
    tech_score: int = Field(default=0, ge=0, le=100, description="技术能力评分")
    communication_score: int = Field(default=0, ge=0, le=100, description="沟通表达评分")
    highlights: list[str] = Field(default_factory=list, description="表现亮点")
    weaknesses: list[str] = Field(default_factory=list, description="答错或不完整清单")
    suggested_review: list[str] = Field(default_factory=list, description="建议复习知识点")
    memory_updates: list[dict] = Field(default_factory=list, description="记忆更新列表")


class ResumeAnalysisResult(BaseModel):
    summary: str = Field(default="", description="简历摘要")
    skills_json: dict[str, list[str]] = Field(default_factory=dict, description="技能矩阵")
    project_highlights: list[str] = Field(default_factory=list, description="项目亮点")
    potential_questions_json: list[str] = Field(default_factory=list, description="潜在追问点")


class JobAnalysisResult(BaseModel):
    summary: str = Field(default="", description="岗位摘要")
    must_have_skills_json: list[str] = Field(default_factory=list, description="核心要求")
    domain: str = Field(default="", description="业务领域")
    level: str = Field(default="", description="岗位级别")
