import json
import re
from pathlib import Path
from typing import Any

from app.core.config import DATA_DIR


SECTION_DIRS = {
    "resume": "resumes",
    "job": "jobs",
    "material": "materials",
    "interview": "interviews",
    "report": "reports",
}


def write_document(
    section: str,
    record_id: str,
    *,
    title: str,
    raw_text: str = "",
    structured: dict[str, Any] | list[Any] | None = None,
    summary: str = "",
) -> str:
    directory = _section_dir(section)
    path = directory / f"{_safe_id(record_id)}.md"
    body = _build_markdown(title=title, raw_text=raw_text, structured=structured, summary=summary)
    path.write_text(body, encoding="utf-8")
    return str(path)


def append_transcript(session_id: str, role: str, content: str) -> str:
    directory = _section_dir("interview")
    path = directory / f"{_safe_id(session_id)}.md"
    if not path.exists():
        path.write_text(f"# Interview Transcript\n\nSession: `{session_id}`\n\n", encoding="utf-8")
    label = "候选人" if role == "user" else "面试官"
    with path.open("a", encoding="utf-8") as f:
        f.write(f"## {label}\n\n{content.strip()}\n\n")
    return str(path)


def write_report(session_id: str, assessment: dict[str, Any] | None) -> str:
    assessment = assessment or {}
    highlights = "\n".join(f"- {item}" for item in assessment.get("highlights", [])) or "- 无"
    weaknesses = "\n".join(f"- {item}" for item in assessment.get("weaknesses", [])) or "- 无"
    reviews = "\n".join(f"- {item}" for item in assessment.get("suggested_review", [])) or "- 无"
    raw_json = json.dumps(assessment, ensure_ascii=False, indent=2)
    content = (
        "# 面试评估报告\n\n"
        f"- 总评分: {assessment.get('total_score', '-')}\n"
        f"- 技术能力: {assessment.get('tech_score', '-')}\n"
        f"- 沟通表达: {assessment.get('communication_score', '-')}\n\n"
        "## 表现亮点\n\n"
        f"{highlights}\n\n"
        "## 薄弱项\n\n"
        f"{weaknesses}\n\n"
        "## 建议复习\n\n"
        f"{reviews}\n\n"
        "## 结构化结果\n\n"
        f"```json\n{raw_json}\n```\n"
    )
    path = _section_dir("report") / f"{_safe_id(session_id)}.md"
    path.write_text(content, encoding="utf-8")
    return str(path)


def _build_markdown(
    *,
    title: str,
    raw_text: str,
    structured: dict[str, Any] | list[Any] | None,
    summary: str,
) -> str:
    parts = [f"# {title.strip() or 'Untitled'}", ""]
    if summary:
        parts.extend(["## Summary", "", summary.strip(), ""])
    if structured is not None:
        parts.extend([
            "## Structured Data",
            "",
            "```json",
            json.dumps(structured, ensure_ascii=False, indent=2),
            "```",
            "",
        ])
    if raw_text:
        parts.extend(["## Raw Text", "", raw_text.strip(), ""])
    return "\n".join(parts)


def _section_dir(section: str) -> Path:
    directory = DATA_DIR / SECTION_DIRS[section]
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _safe_id(record_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", record_id)
