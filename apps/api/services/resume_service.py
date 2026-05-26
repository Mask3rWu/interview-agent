from datetime import datetime

from api.db import repositories
from api.schemas.llm_outputs import ResumeAnalysisResult
from api.schemas.resume import ResumeCreate, ResumeResponse
from api.services import markdown_store


SKILL_KEYWORDS = {
    "backend": ["fastapi", "django", "flask", "spring", "redis", "mysql", "postgres", "kafka"],
    "frontend": ["react", "next", "vue", "tailwind", "typescript", "javascript"],
    "ai": ["langgraph", "langchain", "rag", "llm", "向量", "embedding", "agent"],
    "infra": ["docker", "kubernetes", "linux", "nginx", "ci/cd", "supabase"],
}


def create_resume(data: ResumeCreate) -> ResumeResponse:
    record = data.model_dump()
    analysis = _analyze_resume(data.raw_text)
    record["summary_json"] = {"summary": analysis.summary}
    record["skills_json"] = analysis.skills_json
    record["project_highlights"] = analysis.project_highlights
    record["potential_questions_json"] = analysis.potential_questions_json
    record["markdown_path"] = ""
    record["created_at"] = datetime.now().isoformat()
    record["updated_at"] = record["created_at"]

    saved = repositories.insert("resumes", record)
    markdown_path = markdown_store.write_document(
        "resume",
        saved["id"],
        title=saved["name"],
        raw_text=saved["raw_text"],
        structured=analysis.model_dump(),
        summary=analysis.summary,
    )
    saved = repositories.update("resumes", saved["id"], {"markdown_path": markdown_path}) or saved
    return ResumeResponse(**saved)


def list_resumes() -> list[ResumeResponse]:
    records = repositories.list_all("resumes")
    return [ResumeResponse(**r) for r in records]


def get_resume(resume_id: str) -> ResumeResponse | None:
    record = repositories.get("resumes", resume_id)
    if record is None:
        return None
    return ResumeResponse(**record)


def _analyze_resume(raw_text: str) -> ResumeAnalysisResult:
    lowered = raw_text.lower()
    skills: dict[str, list[str]] = {}
    for category, keywords in SKILL_KEYWORDS.items():
        hits = [kw for kw in keywords if kw in lowered or kw in raw_text]
        if hits:
            skills[category] = hits

    lines = [line.strip("- ").strip() for line in raw_text.splitlines() if line.strip()]
    project_lines = [
        line for line in lines
        if any(token in line for token in ("项目", "系统", "平台", "负责", "实现", "优化"))
    ][:5]
    questions = []
    for highlight in project_lines[:4]:
        questions.append(f"请展开说明：{highlight[:60]}")
    if not questions:
        questions = ["请介绍一段最能体现你技术能力的项目经历。"]

    summary = "；".join(lines[:3])[:240] if lines else "未提供简历摘要。"
    return ResumeAnalysisResult(
        summary=summary,
        skills_json=skills,
        project_highlights=project_lines,
        potential_questions_json=questions,
    )
