"""
Long-term memory service: query, decay, and review scheduling.
"""
import math
from datetime import datetime, timedelta
from typing import Any

from api.db import repositories


HALF_LIFE_DAYS = {
    "low": 3,     # mastery < 0.4
    "mid": 7,     # 0.4 <= mastery < 0.7
    "high": 21,   # mastery >= 0.7
}

MASTERY_ADJUST = {
    "excellent": +0.12,
    "adequate": +0.05,
    "vague": -0.08,
    "wrong": -0.15,
    "unknown": -0.18,
}

WEAK_PERFORMANCES = {"wrong", "vague", "unknown"}


def _get_half_life(score: float) -> int:
    if score < 0.4:
        return HALF_LIFE_DAYS["low"]
    elif score < 0.7:
        return HALF_LIFE_DAYS["mid"]
    else:
        return HALF_LIFE_DAYS["high"]


def list_memories(sort_by: str = "mastery_score") -> list[dict]:
    memories = repositories.list_all("knowledge_memories")
    # Apply decay before returning
    for m in memories:
        _apply_decay(m)
    reverse = sort_by in ("mastery_score", "exposure_count")
    return sorted(memories, key=lambda m: m.get(sort_by, 0), reverse=reverse)


def list_weakness_memories(limit: int = 5) -> list[dict]:
    memories = list_memories(sort_by="mastery_score")
    candidates = [
        m for m in memories
        if m.get("weakness_count", 0) > 0 or m.get("mastery_score", 1.0) < 0.6
    ]
    candidates.sort(key=lambda m: (
        m.get("mastery_score", 1.0),
        -m.get("weakness_count", 0),
        m.get("next_review_at") or "",
    ))
    return candidates[:limit]


def apply_memory_updates(
    memory_updates: list[dict],
    *,
    interview_id: str,
    tested_at: str | None = None,
) -> None:
    if not memory_updates:
        return

    tested_at = tested_at or datetime.now().isoformat()

    for update in memory_updates:
        topic = update.get("topic", "")
        if not topic:
            continue

        perf = update.get("performance", "adequate")
        delta = MASTERY_ADJUST.get(perf, 0.0)
        existing = _find_memory_by_topic(topic)

        if existing:
            _merge_existing_memory(existing, update, perf, delta, interview_id, tested_at)
            repositories.update("knowledge_memories", existing["id"], existing)
        else:
            record = _new_memory_record(update, perf, delta, interview_id, tested_at)
            repositories.insert("knowledge_memories", record)


def rebuild_memories_from_interviews() -> dict:
    interviews = [
        i for i in repositories.list_all("interviews")
        if i.get("status") == "ended"
    ]
    interviews.sort(key=lambda i: i.get("created_at") or "")

    repositories.replace_table("knowledge_memories", {})

    success_count = 0
    failure_count = 0
    update_count = 0
    for interview in interviews:
        assessment = _reassess_interview_record(interview)
        interview["assessment"] = assessment.get("assessment")
        interview["assessment_status"] = assessment.get("assessment_status", "failed")
        interview["assessment_error"] = assessment.get("assessment_error", "")
        interview["memory_updates"] = assessment.get("memory_updates", [])
        repositories.update("interviews", interview["id"], {
            "assessment": interview["assessment"],
            "assessment_status": interview["assessment_status"],
            "assessment_error": interview["assessment_error"],
            "memory_updates": interview["memory_updates"],
        })

        if interview["assessment_status"] == "success" and interview["memory_updates"]:
            apply_memory_updates(
                interview["memory_updates"],
                interview_id=interview.get("id", ""),
                tested_at=interview.get("created_at") or datetime.now().isoformat(),
            )
            update_count += len(interview["memory_updates"])
            success_count += 1
        else:
            failure_count += 1

    return {
        "interview_count": len(interviews),
        "success_count": success_count,
        "failure_count": failure_count,
        "memory_update_count": update_count,
        "memory_count": len(repositories.list_all("knowledge_memories")),
    }


def _apply_decay(memory: dict) -> None:
    last_tested = memory.get("last_tested_at")
    if not last_tested:
        return

    if isinstance(last_tested, str):
        last_tested = datetime.fromisoformat(last_tested)

    now = datetime.now()
    days_since = (now - last_tested.replace(tzinfo=None)).days
    if days_since <= 0:
        return

    half_life = _get_half_life(memory.get("mastery_score", 0.5))
    decay = math.exp(-days_since / half_life)
    memory["mastery_score"] = round(max(0.0, min(1.0, memory["mastery_score"] * decay)), 4)


def _merge_existing_memory(
    memory: dict,
    update: dict,
    perf: str,
    delta: float,
    interview_id: str,
    tested_at: str,
) -> None:
    evidence = _normalize_evidence(memory.get("evidence_json", []))
    if interview_id and any(e.get("interview_id") == interview_id for e in evidence):
        return

    new_score = max(0.0, min(1.0, memory.get("mastery_score", 0.5) + delta))
    if interview_id:
        evidence.append({
            "interview_id": interview_id,
            "performance": perf,
            "timestamp": tested_at,
        })
    source_ids = _source_interview_ids(evidence)
    memory["mastery_score"] = new_score
    memory["exposure_count"] = memory.get("exposure_count", 0) + 1
    if perf in WEAK_PERFORMANCES:
        memory["weakness_count"] = memory.get("weakness_count", 0) + 1
    memory["last_tested_at"] = tested_at
    memory["next_review_at"] = _calc_next_review(new_score, tested_at).isoformat()
    memory["evidence_json"] = evidence[-20:]
    memory["source_interview_ids"] = source_ids[-20:]
    memory["category"] = update.get("category") or memory.get("category", "")
    memory["updated_at"] = datetime.now().isoformat()


def _new_memory_record(update: dict, perf: str, delta: float, interview_id: str, tested_at: str) -> dict:
    new_score = max(0.0, min(1.0, 0.5 + delta))
    evidence = []
    if interview_id:
        evidence.append({
            "interview_id": interview_id,
            "performance": perf,
            "timestamp": tested_at,
        })

    return {
        "topic": update.get("topic", ""),
        "category": update.get("category", ""),
        "mastery_score": new_score,
        "exposure_count": 1,
        "weakness_count": 1 if perf in WEAK_PERFORMANCES else 0,
        "last_tested_at": tested_at,
        "next_review_at": _calc_next_review(new_score, tested_at).isoformat(),
        "evidence_json": evidence,
        "source_interview_ids": _source_interview_ids(evidence),
        "updated_at": datetime.now().isoformat(),
    }


def _normalize_evidence(evidence: list) -> list[dict]:
    normalized = []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "interview_id": item.get("interview_id", ""),
            "performance": item.get("performance", ""),
            "timestamp": item.get("timestamp", ""),
        })
    return normalized


def _source_interview_ids(evidence: list[dict]) -> list[str]:
    ids = []
    for item in evidence:
        interview_id = item.get("interview_id")
        if interview_id and interview_id not in ids:
            ids.append(interview_id)
    return ids


def _find_memory_by_topic(topic: str) -> dict | None:
    all_memories = repositories.list_all("knowledge_memories")
    for m in all_memories:
        if m.get("topic") == topic:
            return m
    return None


def _calc_next_review(score: float, tested_at: str | None = None) -> datetime:
    if score < 0.4:
        days = 1
    elif score < 0.6:
        days = 3
    elif score < 0.8:
        days = 7
    else:
        days = 21

    base = datetime.now()
    if tested_at:
        base = datetime.fromisoformat(tested_at).replace(tzinfo=None)
    return base + timedelta(days=days)


def _reassess_interview_record(interview: dict[str, Any]) -> dict[str, Any]:
    conversation = _build_conversation_text(interview.get("messages", []))
    if not conversation:
        return {
            "assessment": None,
            "assessment_status": "failed",
            "assessment_error": "No conversation available",
            "memory_updates": [],
        }

    from api.services.model_router import get_llm, is_llm_available

    if not is_llm_available():
        return {
            "assessment": None,
            "assessment_status": "failed",
            "assessment_error": "LLM is not configured",
            "memory_updates": [],
        }

    llm = get_llm("assessment")
    if not llm:
        return {
            "assessment": None,
            "assessment_status": "failed",
            "assessment_error": "LLM client unavailable",
            "memory_updates": [],
        }

    try:
        from api.agents.nodes.assessment import evaluate_conversation
        import asyncio

        result = asyncio.run(evaluate_conversation(llm, conversation))
        return {
            "assessment": result,
            "assessment_status": "success",
            "assessment_error": "",
            "memory_updates": result.get("memory_updates", []),
        }
    except Exception as exc:
        return {
            "assessment": None,
            "assessment_status": "failed",
            "assessment_error": f"{type(exc).__name__}: {exc}",
            "memory_updates": [],
        }


def _build_messages_from_transcript(messages_raw: list[dict]) -> list:
    return []


def _build_conversation_text(messages_raw: list[dict]) -> str:
    lines = []
    for m in messages_raw:
        role = m.get("role")
        content = m.get("content", "")
        if role == "user":
            lines.append(f"候选人: {content}")
        elif role == "interviewer":
            lines.append(f"面试官: {content}")
    return "\n".join(lines)
