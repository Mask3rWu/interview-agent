import hashlib
import json
import math
import urllib.error
import urllib.request

from api.core.config import (
    EMBEDDING_API_KEY,
    EMBEDDING_BASE_URL,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    EMBEDDING_PROVIDER,
)


async def embed_text(text: str) -> list[float]:
    """Return an embedding vector.

    A configured provider is used for production retrieval. The deterministic
    local vector keeps tests and local demos usable when no model is configured.
    """
    return embed_text_sync(text)


def embed_text_sync(text: str) -> list[float]:
    if _is_remote_configured():
        return _remote_embedding(text)
    return _local_embedding(text, EMBEDDING_DIMENSIONS)


def embedding_backend() -> str:
    return f"{EMBEDDING_PROVIDER}:{EMBEDDING_MODEL}" if _is_remote_configured() else "local_hash"


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    length = min(len(left), len(right))
    dot = sum(left[i] * right[i] for i in range(length))
    l_norm = math.sqrt(sum(left[i] * left[i] for i in range(length)))
    r_norm = math.sqrt(sum(right[i] * right[i] for i in range(length)))
    if not l_norm or not r_norm:
        return 0.0
    return dot / (l_norm * r_norm)


def _local_embedding(text: str, dimensions: int) -> list[float]:
    dims = max(8, min(dimensions, 1536))
    vector = [0.0] * dims
    tokens = _tokens(text)
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dims
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(v * v for v in vector))
    if not norm:
        return vector
    return [round(v / norm, 8) for v in vector]


def _tokens(text: str) -> list[str]:
    lowered = text.lower()
    words = []
    buf = []
    for ch in lowered:
        if ch.isalnum() or "\u4e00" <= ch <= "\u9fff":
            buf.append(ch)
        elif buf:
            words.append("".join(buf))
            buf = []
    if buf:
        words.append("".join(buf))

    cjk = [ch for ch in lowered if "\u4e00" <= ch <= "\u9fff"]
    bigrams = ["".join(cjk[i:i + 2]) for i in range(max(0, len(cjk) - 1))]
    return words + bigrams


def _is_remote_configured() -> bool:
    return bool(EMBEDDING_MODEL)


def _remote_embedding(text: str) -> list[float]:
    if EMBEDDING_PROVIDER != "openai_compatible":
        raise ValueError(f"Unsupported embedding provider: {EMBEDDING_PROVIDER}")
    if not EMBEDDING_BASE_URL or not EMBEDDING_API_KEY:
        raise ValueError("EMBEDDING_MODEL is set but EMBEDDING_BASE_URL or EMBEDDING_API_KEY is missing")

    payload = {
        "model": EMBEDDING_MODEL,
        "input": text,
        "encoding_format": "float",
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        _embeddings_url(EMBEDDING_BASE_URL),
        data=data,
        headers={
            "Authorization": f"Bearer {EMBEDDING_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"Embedding request failed: HTTP {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Embedding request failed: {exc.reason}") from exc

    body = json.loads(raw)
    rows = body.get("data") or []
    if not rows or "embedding" not in rows[0]:
        raise RuntimeError("Embedding response did not include data[0].embedding")

    embedding = [float(value) for value in rows[0]["embedding"]]
    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            f"Embedding dimension mismatch: got {len(embedding)}, expected {EMBEDDING_DIMENSIONS}"
        )
    return embedding


def _embeddings_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if normalized.endswith("/embeddings"):
        return normalized
    return f"{normalized}/embeddings"
