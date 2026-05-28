from datetime import datetime
from pydantic import BaseModel, Field


class MaterialCreate(BaseModel):
    name: str = Field(description="资料名称")
    type: str = Field(default="markdown", description="资料类型")
    raw_text: str = Field(description="资料内容（Markdown）")


class MaterialResponse(BaseModel):
    id: str
    name: str
    type: str = "markdown"
    raw_text: str
    source_file_path: str | None = None
    markdown_path: str = ""
    enabled: bool = True
    chunk_count: int = 0
    embedding_status: str = "pending"
    processing_error: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
