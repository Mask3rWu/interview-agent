from app.db import repositories
from app.rag.embeddings import cosine_similarity, embed_text_sync


def retrieve_material_context(
    query_text: str,
    material_ids: list[str],
    *,
    top_k: int = 2,
) -> list[dict]:
    if not query_text.strip() or not material_ids:
        return []

    query_embedding = embed_text_sync(query_text)
    try:
        rows = repositories.rpc("match_material_chunks", {
            "query_embedding": query_embedding,
            "match_count": top_k,
            "filter_material_ids": material_ids,
        })
        if rows:
            return rows
    except RuntimeError as exc:
        if "USE_SUPABASE=true" in str(exc):
            raise
    except Exception:
        # Local/demo fallback: if RPC is unavailable, use rows fetched through the repository.
        pass

    candidates = [
        chunk for chunk in repositories.list_all("material_chunks")
        if chunk.get("material_id") in set(material_ids)
    ]
    scored = []
    for chunk in candidates:
        score = cosine_similarity(query_embedding, chunk.get("embedding", []))
        keyword_bonus = _keyword_bonus(query_text, chunk.get("content", ""))
        scored.append({**chunk, "score": round(score + keyword_bonus, 6)})

    scored.sort(key=lambda item: item.get("score", 0), reverse=True)
    return scored[:top_k]


def format_context(chunks: list[dict]) -> str:
    lines = []
    for chunk in chunks:
        metadata = chunk.get("metadata_json") or chunk.get("metadata") or {}
        heading = metadata.get("heading", "")
        label = f"资料片段 {chunk.get('chunk_index', '-')}"
        if heading:
            label += f" / {heading}"
        lines.append(f"[{label}]\n{chunk.get('content', '').strip()}")
    return "\n---\n".join(lines)


def _keyword_bonus(query: str, content: str) -> float:
    query_terms = {term for term in query.lower().split() if len(term) >= 2}
    if not query_terms:
        return 0.0
    content_lower = content.lower()
    hits = sum(1 for term in query_terms if term in content_lower)
    return min(0.2, hits * 0.04)
