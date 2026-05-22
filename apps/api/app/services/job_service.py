from app.core import json_store
from app.schemas.job import JobCreate, JobResponse


def create_job(data: JobCreate) -> JobResponse:
    record = data.model_dump()
    record["must_have_skills_json"] = []
    record["domain"] = ""
    record["level"] = ""
    record["markdown_path"] = ""

    saved = json_store.insert("jobs", record)
    return JobResponse(**saved)


def list_jobs() -> list[JobResponse]:
    records = json_store.list_all("jobs")
    return [JobResponse(**r) for r in records]


def get_job(job_id: str) -> JobResponse | None:
    record = json_store.get("jobs", job_id)
    if record is None:
        return None
    return JobResponse(**record)
