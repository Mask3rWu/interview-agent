from datetime import datetime

from api.db import repositories
from api.schemas.job import JobCreate, JobResponse
from api.schemas.llm_outputs import JobAnalysisResult
from api.services import markdown_store


DOMAIN_KEYWORDS = {
    "backend": ["后端", "服务端", "java", "python", "go", "redis", "mysql", "微服务"],
    "frontend": ["前端", "react", "vue", "next", "typescript", "css"],
    "ai": ["ai", "llm", "大模型", "rag", "agent", "机器学习", "算法"],
    "data": ["数据", "数仓", "spark", "flink", "分析"],
}


def create_job(data: JobCreate) -> JobResponse:
    record = data.model_dump()
    analysis = _analyze_job(data.raw_text)
    record["summary_json"] = {"summary": analysis.summary}
    record["must_have_skills_json"] = analysis.must_have_skills_json
    record["domain"] = analysis.domain
    record["level"] = analysis.level
    record["markdown_path"] = ""
    record["created_at"] = datetime.now().isoformat()
    record["updated_at"] = record["created_at"]

    saved = repositories.insert("jobs", record)
    markdown_path = markdown_store.write_document(
        "job",
        saved["id"],
        title=f"{saved.get('company', '')} {saved['name']}".strip(),
        raw_text=saved["raw_text"],
        structured=analysis.model_dump(),
        summary=analysis.summary,
    )
    saved = repositories.update("jobs", saved["id"], {"markdown_path": markdown_path}) or saved
    return JobResponse(**saved)


def list_jobs() -> list[JobResponse]:
    records = repositories.list_all("jobs")
    return [JobResponse(**r) for r in records]


def get_job(job_id: str) -> JobResponse | None:
    record = repositories.get("jobs", job_id)
    if record is None:
        return None
    return JobResponse(**record)


def _analyze_job(raw_text: str) -> JobAnalysisResult:
    lowered = raw_text.lower()
    domain = ""
    for candidate, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in lowered or keyword in raw_text for keyword in keywords):
            domain = candidate
            break

    level = ""
    if any(token in raw_text for token in ("高级", "资深", "专家", "架构师")):
        level = "senior"
    elif any(token in raw_text for token in ("实习", "校招", "初级")):
        level = "junior"
    elif raw_text:
        level = "mid"

    lines = [line.strip("-* 0123456789.").strip() for line in raw_text.splitlines() if line.strip()]
    skill_lines = [
        line for line in lines
        if any(token in line.lower() for token in ("熟悉", "掌握", "经验", "react", "python", "java", "redis", "mysql", "rag", "llm"))
    ][:8]
    summary = "；".join(lines[:3])[:240] if lines else "未提供 JD 摘要。"
    return JobAnalysisResult(
        summary=summary,
        must_have_skills_json=skill_lines,
        domain=domain,
        level=level,
    )
