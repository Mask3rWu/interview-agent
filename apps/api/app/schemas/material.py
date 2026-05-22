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
    markdown_path: str = ""
    enabled: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
