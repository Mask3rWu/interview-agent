"""Repository helpers with Supabase PostgREST and local JSON backends."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from app.core import json_store
from app.core.config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL, USE_SUPABASE


TABLE_MAP = {
    "resumes": "resume_profiles",
    "jobs": "job_profiles",
    "materials": "materials",
    "material_chunks": "material_chunks",
    "interviews": "interview_sessions",
    "knowledge_memories": "knowledge_memories",
}

PUBLIC_COLUMNS = {
    "resume_profiles": "id,name,source_file_path,markdown_path,raw_text,summary_json,skills_json,potential_questions_json,project_highlights,created_at,updated_at",
    "job_profiles": "id,name,company,raw_text,markdown_path,summary_json,must_have_skills_json,domain,level,created_at,updated_at",
    "materials": "id,name,type,raw_text,source_file_path,markdown_path,enabled,chunk_count,embedding_status,created_at",
    "material_chunks": "id,material_id,chunk_index,content,embedding,metadata_json,created_at",
    "interview_sessions": "id,resume_profile_id,job_profile_id,selected_material_ids,status,messages,current_topic,covered_topics,follow_up_count,unclear_count,current_round,max_rounds,assessment,assessment_status,assessment_error,memory_updates,transcript_path,report_path,router_source,retrieved_context,created_at,ended_at",
    "knowledge_memories": "id,topic,category,mastery_score,exposure_count,weakness_count,last_tested_at,next_review_at,evidence_json,source_interview_ids,updated_at",
}


def insert(table: str, record: dict) -> dict:
    if USE_SUPABASE:
        rows = _request(
            "POST",
            _path(table, {"select": PUBLIC_COLUMNS[_table(table)]}),
            body=_strip_none(record),
            prefer="return=representation",
        )
        return rows[0]
    return json_store.insert(table, record)


def get(table: str, record_id: str) -> dict | None:
    if USE_SUPABASE:
        rows = _request(
            "GET",
            _path(table, {
                "select": PUBLIC_COLUMNS[_table(table)],
                "id": f"eq.{record_id}",
                "limit": "1",
            }),
        )
        return rows[0] if rows else None
    return json_store.get(table, record_id)


def list_all(table: str) -> list[dict]:
    if USE_SUPABASE:
        db_table = _table(table)
        params = {"select": PUBLIC_COLUMNS[db_table]}
        if db_table in {"resume_profiles", "job_profiles", "materials", "interview_sessions"}:
            params["order"] = "created_at.desc"
        elif db_table == "knowledge_memories":
            params["order"] = "updated_at.desc"
        return _request("GET", _path(table, params))
    return json_store.list_all(table)


def update(table: str, record_id: str, record: dict) -> dict | None:
    if USE_SUPABASE:
        rows = _request(
            "PATCH",
            _path(table, {
                "id": f"eq.{record_id}",
                "select": PUBLIC_COLUMNS[_table(table)],
            }),
            body=_strip_none(record),
            prefer="return=representation",
        )
        return rows[0] if rows else None
    return json_store.update(table, record_id, record)


def replace_table(table: str, records: dict) -> None:
    if USE_SUPABASE:
        _request(
            "DELETE",
            _path(table, {"id": "neq.00000000-0000-0000-0000-000000000000"}),
        )
        if records:
            _request("POST", _path(table), body=list(records.values()))
        return
    json_store.replace_table(table, records)


def delete(table: str, record_id: str) -> bool:
    if USE_SUPABASE:
        _request("DELETE", _path(table, {"id": f"eq.{record_id}"}))
        return True
    return json_store.delete(table, record_id)


def rpc(function_name: str, payload: dict) -> Any:
    if USE_SUPABASE:
        return _request("POST", f"rpc/{function_name}", body=payload)
    raise RuntimeError("RPC calls require USE_SUPABASE=true")


def _request(
    method: str,
    path: str,
    *,
    body: dict | list | None = None,
    prefer: str | None = None,
) -> Any:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("USE_SUPABASE=true but SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is missing")

    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Accept": "application/json",
    }
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    if prefer:
        headers["Prefer"] = prefer

    req = urllib.request.Request(
        f"{SUPABASE_URL.rstrip()}/rest/v1/{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"Supabase {method} {path} failed: HTTP {exc.code} {detail}") from exc

    if not raw:
        return []
    return json.loads(raw)


def _path(table: str, params: dict[str, str] | None = None) -> str:
    encoded = urllib.parse.urlencode(params or {}, safe=".,:*")
    return f"{_table(table)}?{encoded}" if encoded else _table(table)


def _table(table: str) -> str:
    return TABLE_MAP.get(table, table)


def _strip_none(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if value is not None}
