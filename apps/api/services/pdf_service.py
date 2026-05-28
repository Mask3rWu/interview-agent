import asyncio
import unicodedata
import re
from dataclasses import dataclass
from pathlib import Path

from api.core.config import (
    DATA_DIR,
    PDF_IMAGE_CONCURRENCY,
    PDF_IMAGE_DPI,
    PDF_MAX_IMAGES_PER_PAGE,
    PDF_MAX_PAGES,
)
from api.services.vision_service import describe_pdf_image


IMAGE_MARKER_RE = re.compile(r"<!-- pdf-image:page=(\d+),index=(\d+) -->")
PAGE_HEADING_RE = re.compile(r"^\s*#{1,6}\s*Page\s+\d+\s*$", re.IGNORECASE)
PAGE_TEXT_RE = re.compile(r"^\s*Page\s+\d+\s*$", re.IGNORECASE)
HEADING_NUMBER_RE = re.compile(r"^(\d+(?:\.\d+){1,4})\s*(.+)$")
CHINESE_HEADING_RE = re.compile(r"^[一二三四五六七八九十百]+、\s*(.+)$")
LIST_MARKER_RE = re.compile(r"^([•◦])\s*(.*)$")
ORDERED_LIST_RE = re.compile(r"^\d+[.)、]\s+.+")


@dataclass
class PdfExtraction:
    markdown: str
    image_count: int
    page_count: int


@dataclass
class PdfImage:
    page_number: int
    image_index: int
    path: Path
    marker: str


def extract_pdf_markdown(pdf_path: Path, material_id: str) -> PdfExtraction:
    page_count = _page_count(pdf_path)
    page_limit = min(page_count, PDF_MAX_PAGES)
    markdown, images = _extract_text_layer_markdown(pdf_path, page_limit, material_id)
    if _looks_sparse_or_corrupted(markdown):
        markdown = _convert_pdf_to_markdown(pdf_path, page_limit)
        images = _extract_pdf_images(pdf_path, material_id)
        if images:
            markdown = _append_image_markers(markdown, images)
    if _looks_corrupted(markdown):
        markdown, images = _extract_text_layer_markdown(pdf_path, page_limit, material_id)
    if page_count > PDF_MAX_PAGES:
        markdown = f"{markdown.rstrip()}\n\n> PDF 页数超过限制，仅处理前 {PDF_MAX_PAGES} 页。"
    return PdfExtraction(
        markdown=normalize_index_markdown(markdown),
        image_count=len(images),
        page_count=page_count,
    )


async def enrich_pdf_images(markdown: str, material_id: str) -> str:
    image_dir = DATA_DIR / "material_images" / material_id
    matches = list(IMAGE_MARKER_RE.finditer(markdown))
    if not matches:
        return normalize_index_markdown(markdown)

    concurrency = max(1, PDF_IMAGE_CONCURRENCY)
    semaphore = asyncio.Semaphore(concurrency)

    async def describe(match: re.Match) -> tuple[str, str]:
        page_number = int(match.group(1))
        image_index = int(match.group(2))
        image_path = image_dir / f"page_{page_number:04d}_image_{image_index:02d}.png"
        marker = match.group(0)
        if not image_path.exists():
            return marker, "图片内容：图片文件未生成。"
        try:
            async with semaphore:
                description = await describe_pdf_image(image_path)
            return marker, f"图片内容：{_single_paragraph(description, 194)}"
        except Exception as exc:
            return marker, f"图片内容：识别失败：{type(exc).__name__}: {exc}"

    replacements = dict(await asyncio.gather(*(describe(match) for match in matches)))
    enriched = markdown
    for marker, replacement in replacements.items():
        enriched = enriched.replace(marker, replacement)
    return normalize_index_markdown(enriched)


def normalize_index_markdown(markdown: str) -> str:
    markdown = markdown.replace("\r\n", "\n").replace("\r", "\n")
    markdown = markdown.replace("\u200b", "").replace("\ufeff", "")
    markdown = re.sub(r"[ \t]+\n", "\n", markdown)
    markdown = _normalize_page_headings(markdown)
    markdown = _normalize_lines(markdown)
    markdown = _merge_wrapped_lines(markdown)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    return markdown.strip()


def _convert_pdf_to_markdown(pdf_path: Path, page_limit: int) -> str:
    try:
        import pymupdf4llm
    except ImportError as exc:
        raise RuntimeError(
            "pymupdf4llm is required for PDF processing. Install dependencies from apps/api/requirements.txt."
        ) from exc

    parts = []
    for page_index in range(page_limit):
        try:
            page_markdown = pymupdf4llm.to_markdown(str(pdf_path), pages=[page_index])
        except TypeError:
            page_markdown = pymupdf4llm.to_markdown(str(pdf_path))
            if page_index > 0:
                break
        if not isinstance(page_markdown, str):
            page_markdown = "\n".join(str(part) for part in page_markdown)
        if page_markdown.strip():
            parts.append(f"<!-- page:{page_index + 1} -->\n\n{page_markdown.strip()}")
    return "\n\n".join(parts)


def _looks_corrupted(markdown: str) -> bool:
    if not markdown.strip():
        return True
    replacement_count = markdown.count("�")
    compatibility_count = sum(1 for ch in markdown if "\u2e80" <= ch <= "\u2eff" or "\u2f00" <= ch <= "\u2fdf")
    cjk_count = sum(1 for ch in markdown if "\u4e00" <= ch <= "\u9fff")
    if replacement_count >= 5:
        return True
    return bool(cjk_count and compatibility_count / max(cjk_count, 1) > 0.05)


def _looks_sparse_or_corrupted(markdown: str) -> bool:
    if _looks_corrupted(markdown):
        return True
    visible_chars = sum(1 for ch in markdown if not ch.isspace())
    return visible_chars < 200


def _extract_text_layer_markdown(
    pdf_path: Path,
    page_limit: int,
    material_id: str | None = None,
) -> tuple[str, list[PdfImage]]:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF processing. Install dependencies from apps/api/requirements.txt.") from exc

    parts: list[str] = []
    images: list[PdfImage] = []
    image_dir = DATA_DIR / "material_images" / material_id if material_id else None
    if image_dir:
        image_dir.mkdir(parents=True, exist_ok=True)

    with fitz.open(pdf_path) as doc:
        for page_index in range(page_limit):
            page = doc[page_index]
            page_number = page_index + 1
            parts.append(f"<!-- page:{page_index + 1} -->")
            image_on_page = 0
            blocks = page.get_text("dict").get("blocks", [])
            blocks.sort(key=lambda block: (
                round(block.get("bbox", [0, 0, 0, 0])[1], 1),
                round(block.get("bbox", [0, 0, 0, 0])[0], 1),
            ))
            for block in blocks:
                block_type = block.get("type")
                if block_type == 0:
                    block_text = _text_block_to_markdown(block)
                    if block_text:
                        parts.append(block_text)
                elif (
                    block_type == 1
                    and image_dir is not None
                    and image_on_page < PDF_MAX_IMAGES_PER_PAGE
                ):
                    bbox = block.get("bbox")
                    if not bbox:
                        continue
                    image_on_page += 1
                    image_path = image_dir / f"page_{page_number:04d}_image_{image_on_page:02d}.png"
                    _render_block_image(page, bbox, image_path)
                    image = PdfImage(
                        page_number=page_number,
                        image_index=image_on_page,
                        path=image_path,
                        marker=f"<!-- pdf-image:page={page_number},index={image_on_page} -->",
                    )
                    images.append(image)
                    parts.append(image.marker)
    return "\n\n".join(parts), images


def _text_block_to_markdown(block: dict) -> str:
    lines = _lines_from_block(block)
    if not lines:
        return ""
    text = "\n".join(line["text"] for line in lines).strip()
    if not text:
        return ""

    max_size = max(line["size"] for line in lines)
    min_x = min(line["x"] for line in lines)
    one_line = " ".join(line["text"] for line in lines).strip()
    one_line = _clean_text(one_line)
    if not one_line:
        return ""

    if _is_code_block(lines):
        return "```text\n" + "\n".join(line["text"] for line in lines) + "\n```"
    list_line = _text_layer_list_line(one_line, min_x)
    if list_line:
        return list_line
    heading = _text_layer_heading(one_line, max_size)
    if heading:
        return heading
    return text


def _lines_from_block(block: dict) -> list[dict]:
    lines = []
    for line in block.get("lines", []):
        spans = []
        for span in line.get("spans", []):
            text = _clean_text(span.get("text", ""))
            if text:
                spans.append(text)
        text = "".join(spans).strip()
        if not text:
            continue
        sizes = [
            span.get("size", 0)
            for span in line.get("spans", [])
            if _clean_text(span.get("text", ""))
        ]
        fonts = [
            span.get("font", "")
            for span in line.get("spans", [])
            if _clean_text(span.get("text", ""))
        ]
        bbox = line.get("bbox", [0, 0, 0, 0])
        lines.append({
            "text": text,
            "size": max(sizes) if sizes else 0,
            "font": " ".join(fonts),
            "x": bbox[0],
        })
    return lines


def _clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u200b", "").replace("\ufeff", "")
    text = " ".join(text.split())
    return text.strip()


def _is_code_block(lines: list[dict]) -> bool:
    if len(lines) < 3:
        return False
    code_font_lines = sum(1 for line in lines if "SourceCode" in line["font"] or "Mono" in line["font"])
    numbered_lines = sum(1 for line in lines if re.fullmatch(r"\d+", line["text"]))
    return code_font_lines >= 2 or numbered_lines >= 3


def _text_layer_list_line(text: str, x: float) -> str:
    marker_match = LIST_MARKER_RE.match(text)
    if marker_match:
        indent = "  " if marker_match.group(1) == "◦" or x > 40 else ""
        content = marker_match.group(2).strip()
        return f"{indent}- {content}" if content else f"{indent}-"
    if text in {"•", "◦"}:
        return ""
    return ""


def _text_layer_heading(text: str, size: float) -> str:
    numbered = HEADING_NUMBER_RE.match(text)
    if numbered and size >= 13:
        level = min(numbered.group(1).count(".") + 1, 4)
        return f"{'#' * level} {_spaced_number_heading(text)}"
    if CHINESE_HEADING_RE.match(text) and size >= 16:
        return f"## {text}"
    if size >= 22 and len(text) <= 80:
        return f"# {text}"
    if size >= 15 and len(text) <= 80 and not text.endswith(("。", "，", "；")):
        return f"## {text}"
    if size >= 13 and len(text) <= 60 and not text.endswith(("。", "，", "；")):
        return f"### {text}"
    return ""


def _page_count(pdf_path: Path) -> int:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF processing. Install dependencies from apps/api/requirements.txt.") from exc

    with fitz.open(pdf_path) as doc:
        return doc.page_count


def _extract_pdf_images(pdf_path: Path, material_id: str) -> list[PdfImage]:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF image rendering.") from exc

    image_dir = DATA_DIR / "material_images" / material_id
    image_dir.mkdir(parents=True, exist_ok=True)
    images: list[PdfImage] = []

    with fitz.open(pdf_path) as doc:
        page_limit = min(doc.page_count, PDF_MAX_PAGES)
        for page_index in range(page_limit):
            page = doc[page_index]
            page_number = page_index + 1
            image_on_page = 0
            blocks = page.get_text("dict").get("blocks", [])
            blocks.sort(key=lambda block: (
                round(block.get("bbox", [0, 0, 0, 0])[1], 1),
                round(block.get("bbox", [0, 0, 0, 0])[0], 1),
            ))
            for block in blocks:
                if block.get("type") != 1 or image_on_page >= PDF_MAX_IMAGES_PER_PAGE:
                    continue
                bbox = block.get("bbox")
                if not bbox:
                    continue
                image_on_page += 1
                image_path = image_dir / f"page_{page_number:04d}_image_{image_on_page:02d}.png"
                _render_block_image(page, bbox, image_path)
                images.append(PdfImage(
                    page_number=page_number,
                    image_index=image_on_page,
                    path=image_path,
                    marker=f"<!-- pdf-image:page={page_number},index={image_on_page} -->",
                ))
    return images


def _append_image_markers(markdown: str, images: list[PdfImage]) -> str:
    markers = "\n\n".join(image.marker for image in images)
    return f"{markdown.rstrip()}\n\n{markers}" if markdown.strip() else markers


def _render_block_image(page, bbox, image_path: Path) -> None:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF image rendering.") from exc

    rect = fitz.Rect(bbox)
    matrix = fitz.Matrix(PDF_IMAGE_DPI / 72, PDF_IMAGE_DPI / 72)
    pixmap = page.get_pixmap(matrix=matrix, clip=rect, alpha=False)
    pixmap.save(image_path)


def _normalize_page_headings(markdown: str) -> str:
    lines = []
    for line in markdown.splitlines():
        if PAGE_HEADING_RE.match(line) or PAGE_TEXT_RE.match(line):
            continue
        lines.append(line)
    return "\n".join(lines)


def _normalize_lines(markdown: str) -> str:
    normalized = []
    in_fence = False
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            normalized.append(line)
            continue
        if in_fence:
            normalized.append(raw_line.rstrip())
            continue
        if not line:
            normalized.append("")
            continue

        marker_match = IMAGE_MARKER_RE.match(line)
        if marker_match:
            normalized.append(line)
            continue

        line = _normalize_list_line(line)
        line = _normalize_heading_line(line)
        normalized.append(line)
    return "\n".join(normalized)


def _normalize_list_line(line: str) -> str:
    match = LIST_MARKER_RE.match(line)
    if not match:
        return line
    indent = "  " if match.group(1) == "◦" else ""
    content = match.group(2).strip()
    return f"{indent}- {content}" if content else f"{indent}-"


def _normalize_heading_line(line: str) -> str:
    if line.startswith("#"):
        text = line.lstrip("#").strip()
        numbered = HEADING_NUMBER_RE.match(text)
        if numbered:
            level = min(numbered.group(1).count(".") + 1, 4)
            return f"{'#' * level} {_spaced_number_heading(text)}"
        if CHINESE_HEADING_RE.match(text):
            return f"## {text}"
        return line

    numbered = HEADING_NUMBER_RE.match(line)
    if numbered and len(numbered.group(2)) <= 60:
        level = min(numbered.group(1).count(".") + 1, 4)
        return f"{'#' * level} {_spaced_number_heading(line)}"
    if CHINESE_HEADING_RE.match(line) and len(line) <= 40:
        return f"## {line}"
    return line


def _merge_wrapped_lines(markdown: str) -> str:
    result: list[str] = []
    paragraph = ""
    in_fence = False

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped.startswith("```"):
            if paragraph:
                result.append(paragraph)
                paragraph = ""
            result.append(line)
            in_fence = not in_fence
            continue
        if in_fence:
            result.append(line)
            continue
        if not stripped:
            if paragraph:
                result.append(paragraph)
                paragraph = ""
            if result and result[-1] != "":
                result.append("")
            continue
        if _is_block_boundary(stripped):
            if paragraph:
                result.append(paragraph)
                paragraph = ""
            result.append(stripped)
            continue
        if not paragraph:
            paragraph = stripped
        elif _should_join_without_space(paragraph, stripped):
            paragraph += stripped
        else:
            paragraph += " " + stripped

    if paragraph:
        result.append(paragraph)
    return "\n".join(result)


def _is_block_boundary(line: str) -> bool:
    return (
        line.startswith("#")
        or line.startswith("- ")
        or line.startswith("  - ")
        or line.startswith(">")
        or line.startswith("图片内容：")
        or IMAGE_MARKER_RE.match(line) is not None
        or ORDERED_LIST_RE.match(line) is not None
    )


def _should_join_without_space(left: str, right: str) -> bool:
    if not left or not right:
        return False
    return _is_cjk(left[-1]) and _is_cjk(right[0])


def _is_cjk(ch: str) -> bool:
    return "\u4e00" <= ch <= "\u9fff"


def _single_paragraph(content: str, limit: int) -> str:
    content = re.sub(r"^[#>\-*\d.、)）\s]+", "", content.replace("\r", "\n"), flags=re.MULTILINE)
    content = " ".join(part.strip() for part in content.splitlines() if part.strip())
    content = " ".join(content.split())
    if len(content) <= limit:
        return content
    return content[:limit].rstrip("，。；、,. ;") + "。"


def _spaced_number_heading(text: str) -> str:
    return re.sub(r"^(\d+(?:\.\d+){0,4})\s*", r"\1 ", text, count=1)
