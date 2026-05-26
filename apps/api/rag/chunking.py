"""
Simple text chunking for RAG materials.
Splits markdown/text by headings and length.
"""
import re


def chunk_text(text: str, max_chars: int = 1000, overlap: int = 150) -> list[dict]:
    """
    Split text into chunks, preserving markdown heading context.
    Returns list of {"content": str, "metadata": {"heading": str, "chunk_index": int}}.
    """
    # Try to split by headings first
    sections = re.split(r"(?=^#{1,3}\s)", text, flags=re.MULTILINE)

    chunks = []
    index = 0

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract heading if present
        heading_match = re.match(r"^(#{1,3})\s+(.+)", section)
        heading = heading_match.group(2) if heading_match else ""

        # If section is short enough, keep as one chunk
        if len(section) <= max_chars:
            chunks.append({
                "content": section,
                "metadata": {"heading": heading, "chunk_index": index},
            })
            index += 1
        else:
            # Split long sections with overlap
            sub_chunks = _split_long_text(section, max_chars, overlap)
            for sc in sub_chunks:
                chunks.append({
                    "content": sc,
                    "metadata": {"heading": heading, "chunk_index": index},
                })
                index += 1

    return chunks


def _split_long_text(text: str, max_chars: int, overlap: int) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap if end < len(text) else end
    return chunks
