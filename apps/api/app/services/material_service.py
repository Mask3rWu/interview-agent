from app.core import json_store
from app.schemas.material import MaterialCreate, MaterialResponse


def create_material(data: MaterialCreate) -> MaterialResponse:
    record = data.model_dump()
    record["enabled"] = True
    record["markdown_path"] = ""

    saved = json_store.insert("materials", record)
    return MaterialResponse(**saved)


def list_materials() -> list[MaterialResponse]:
    records = json_store.list_all("materials")
    return [MaterialResponse(**r) for r in records]


def get_material(material_id: str) -> MaterialResponse | None:
    record = json_store.get("materials", material_id)
    if record is None:
        return None
    return MaterialResponse(**record)
