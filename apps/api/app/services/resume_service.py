from app.core import json_store
from app.schemas.resume import ResumeCreate, ResumeResponse


def create_resume(data: ResumeCreate) -> ResumeResponse:
    record = data.model_dump()
    record["skills_json"] = {}
    record["potential_questions_json"] = []
    record["markdown_path"] = ""

    saved = json_store.insert("resumes", record)
    return ResumeResponse(**saved)


def list_resumes() -> list[ResumeResponse]:
    records = json_store.list_all("resumes")
    return [ResumeResponse(**r) for r in records]


def get_resume(resume_id: str) -> ResumeResponse | None:
    record = json_store.get("resumes", resume_id)
    if record is None:
        return None
    return ResumeResponse(**record)
