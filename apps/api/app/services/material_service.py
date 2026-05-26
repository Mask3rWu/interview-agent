from datetime import datetime

from app.db import repositories
from app.rag.chunking import chunk_text
from app.rag.embeddings import embed_text_sync, embedding_backend
from app.schemas.material import MaterialCreate, MaterialResponse
from app.services import markdown_store


def create_material(data: MaterialCreate) -> MaterialResponse:
    record = data.model_dump()
    record["enabled"] = True
    record["markdown_path"] = ""
    record["chunk_count"] = 0
    record["embedding_status"] = "pending"
    record["created_at"] = datetime.now().isoformat()

    saved = repositories.insert("materials", record)
    chunks = chunk_text(data.raw_text)
    for chunk in chunks:
        repositories.insert("material_chunks", {
            "material_id": saved["id"],
            "chunk_index": chunk["metadata"]["chunk_index"],
            "content": chunk["content"],
            "embedding": embed_text_sync(chunk["content"]),
            "metadata_json": {
                **chunk.get("metadata", {}),
                "embedding_backend": embedding_backend(),
            },
            "created_at": datetime.now().isoformat(),
        })

    markdown_path = markdown_store.write_document(
        "material",
        saved["id"],
        title=saved["name"],
        raw_text=saved["raw_text"],
        structured={"chunk_count": len(chunks), "embedding_backend": embedding_backend()},
        summary=f"{len(chunks)} chunks indexed for retrieval.",
    )
    saved = repositories.update("materials", saved["id"], {
        "markdown_path": markdown_path,
        "chunk_count": len(chunks),
        "embedding_status": "ready" if chunks else "empty",
    }) or saved
    return MaterialResponse(**saved)


def list_materials() -> list[MaterialResponse]:
    records = repositories.list_all("materials")
    return [MaterialResponse(**r) for r in records]


def get_material(material_id: str) -> MaterialResponse | None:
    record = repositories.get("materials", material_id)
    if record is None:
        return None
    return MaterialResponse(**record)
