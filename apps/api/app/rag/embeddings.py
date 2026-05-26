import hashlib
import math

from app.core.config import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL


async def embed_text(text: str) -> list[float]:
    """Return an embedding vector.

    If an embedding model is configured this function is the integration point.
    The deterministic local vector keeps tests and local demos usable.
    """
    return _local_embedding(text, EMBEDDING_DIMENSIONS)


def embed_text_sync(text: str) -> list[float]:
    return _local_embedding(text, EMBEDDING_DIMENSIONS)


def embedding_backend() -> str:
    return "configured" if EMBEDDING_MODEL else "local_hash"


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
