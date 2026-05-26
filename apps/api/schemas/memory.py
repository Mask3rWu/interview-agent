from datetime import datetime
from pydantic import BaseModel, Field


class KnowledgeMemory(BaseModel):
    id: str
    topic: str
    category: str = ""
    mastery_score: float = 0.5
    exposure_count: int = 0
    weakness_count: int = 0
    last_tested_at: str | None = None
    next_review_at: str | None = None
    evidence_json: list = Field(default_factory=list)
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class MemoryUpdate(BaseModel):
    topic: str
    category: str = ""
    performance: str = "adequate"  # excellent, adequate, vague, wrong, unknown
    evidence: str = ""
