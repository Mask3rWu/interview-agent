import base64
import mimetypes
from pathlib import Path

from langchain_core.messages import HumanMessage

from api.services.model_router import get_llm, is_agent_llm_available


PDF_IMAGE_PROMPT = (
    "请识别这张 PDF 资料中的图片内容。"
    "输出中文，只用一整段话概括图表结论、流程、架构、代码或截图文字。"
    "不要输出 Markdown、标题、编号、分点列表或学习建议。"
    "不要扩写原图没有的信息。控制在 200 字以内。"
)


async def describe_pdf_image(image_path: Path) -> str:
    if not is_agent_llm_available("pdf_vision"):
        return "未配置 PDF 图片识别模型，跳过图片内容识别。"

    llm = get_llm("pdf_vision")
    if llm is None:
        return "PDF 图片识别模型不可用，跳过图片内容识别。"

    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
    image_data = base64.b64encode(image_path.read_bytes()).decode("ascii")
    message = HumanMessage(content=[
        {"type": "text", "text": PDF_IMAGE_PROMPT},
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
    ])
    response = await llm.ainvoke([message])
    content = response.content if response else ""
    if isinstance(content, list):
        content = "\n".join(str(item) for item in content)
    return _compact_image_description(str(content).strip()) or "图片内容识别为空。"


def _compact_image_description(content: str, limit: int = 200) -> str:
    content = content.replace("\r", "\n")
    lines = []
    for line in content.splitlines():
        line = line.strip()
        line = line.lstrip("#> -*•◦0123456789.、)） \t")
        if line:
            lines.append(line)
    compact = " ".join(lines)
    compact = " ".join(compact.split())
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip("，。；、,. ;") + "。"
