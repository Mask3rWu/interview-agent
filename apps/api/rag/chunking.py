"""
Simple text chunking for RAG materials.
Splits markdown/text by headings and length.
"""
import re


PAGE_HEADING_RE = re.compile(r"^#{1,6}\s*Page\s+\d+\s*$", re.IGNORECASE)
PAGE_MARKER_RE = re.compile(r"<!--\s*page:(\d+)\s*-->")


def chunk_text(text: str, max_chars: int = 1000, overlap: int = 150) -> list[dict]:
    """
    Split text into chunks, preserving markdown heading context.
    Returns list of {"content": str, "metadata": {"heading": str, "chunk_index": int}}.
    """
    text = _strip_page_headings(text)
    sections = re.split(r"(?=^#{1,4}\s)", text, flags=re.MULTILINE)

    chunks = []
    index = 0
    current_page: int | None = None

    for section in sections:
        section = section.strip()
        if not section:
            continue
        section, page_start, page_end = _extract_page_metadata(section, current_page)
        if page_end is not None:
            current_page = page_end
        if not section.strip():
            continue

        # Extract heading if present
        heading_match = re.match(r"^(#{1,4})\s+(.+)", section)
        heading = heading_match.group(2) if heading_match else ""
        metadata = {"heading": heading, "chunk_index": index}
        if page_start is not None:
            metadata["page_start"] = page_start
        if page_end is not None:
            metadata["page_end"] = page_end

        # If section is short enough, keep as one chunk
        if len(section) <= max_chars:
            chunks.append({
                "content": section,
                "metadata": metadata,
            })
            index += 1
        else:
            # Split long sections with overlap
            sub_chunks = _split_long_text(section, max_chars, overlap)
            for sc in sub_chunks:
                chunk_metadata = {**metadata, "chunk_index": index}
                chunks.append({
                    "content": sc,
                    "metadata": chunk_metadata,
                })
                index += 1

    return chunks


def _strip_page_headings(text: str) -> str:
    lines = [
        line for line in text.splitlines()
        if not PAGE_HEADING_RE.match(line.strip())
    ]
    return "\n".join(lines)


def _extract_page_metadata(section: str, fallback_page: int | None) -> tuple[str, int | None, int | None]:
    pages = [int(match.group(1)) for match in PAGE_MARKER_RE.finditer(section)]
    cleaned = PAGE_MARKER_RE.sub("", section).strip()
    if pages:
        return cleaned, pages[0], pages[-1]
    return cleaned, fallback_page, fallback_page


def _split_long_text(text: str, max_chars: int, overlap: int) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap if end < len(text) else end
    return chunks
