import asyncio
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

from api.core.config import DATA_DIR
from api.db import repositories
from api.rag.chunking import chunk_text
from api.rag.embeddings import embed_text_sync, embedding_backend
from api.schemas.material import MaterialCreate, MaterialResponse
from api.services import markdown_store, pdf_service


def create_material(data: MaterialCreate) -> MaterialResponse:
    record = data.model_dump()
    record["enabled"] = True
    record["markdown_path"] = ""
    record["chunk_count"] = 0
    record["embedding_status"] = "pending"
    record["processing_error"] = ""
    record["created_at"] = datetime.now().isoformat()

    saved = repositories.insert("materials", record)
    saved = _index_material_text(saved, data.raw_text)
    return MaterialResponse(**saved)


async def create_pdf_material(name: str, upload: UploadFile) -> MaterialResponse:
    filename = upload.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are supported")

    record = {
        "name": name,
        "type": "pdf",
        "raw_text": "",
        "source_file_path": "",
        "markdown_path": "",
        "enabled": True,
        "chunk_count": 0,
        "embedding_status": "processing",
        "processing_error": "",
        "created_at": datetime.now().isoformat(),
    }
    saved = repositories.insert("materials", record)
    upload_dir = DATA_DIR / "material_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    target_path = upload_dir / f"{saved['id']}.pdf"
    with target_path.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    saved = repositories.update("materials", saved["id"], {
        "source_file_path": str(target_path),
    }) or saved
    return MaterialResponse(**saved)


def process_pdf_material(material_id: str) -> None:
    record = repositories.get("materials", material_id)
    if not record:
        return
    try:
        repositories.update("materials", material_id, {
            "embedding_status": "extracting",
            "processing_error": "",
        })
        source_path = Path(record.get("source_file_path") or "")
        extraction = pdf_service.extract_pdf_markdown(source_path, material_id)

        repositories.update("materials", material_id, {
            "embedding_status": "vision_processing" if extraction.image_count else "indexing",
            "raw_text": extraction.markdown,
        })

        markdown = asyncio.run(pdf_service.enrich_pdf_images(extraction.markdown, material_id))
        latest = repositories.get("materials", material_id) or record
        latest["raw_text"] = markdown
        latest = repositories.update("materials", material_id, {
            "raw_text": markdown,
            "embedding_status": "indexing",
        }) or latest
        _index_material_text(latest, markdown, extra_structured={
            "pdf_page_count": extraction.page_count,
            "pdf_image_count": extraction.image_count,
        })
    except Exception as exc:
        repositories.update("materials", material_id, {
            "embedding_status": "failed",
            "processing_error": f"{type(exc).__name__}: {exc}",
        })


def reprocess_pdf_material(material_id: str) -> MaterialResponse:
    record = repositories.get("materials", material_id)
    if not record:
        raise ValueError("Material not found")
    if record.get("type") != "pdf" or not record.get("source_file_path"):
        raise ValueError("Only uploaded PDF materials can be reprocessed")
    process_pdf_material(material_id)
    latest = repositories.get("materials", material_id) or record
    return MaterialResponse(**latest)


def _index_material_text(record: dict, raw_text: str, extra_structured: dict | None = None) -> dict:
    chunks = chunk_text(raw_text)
    repositories.delete_material_chunks(record["id"])
    for chunk in chunks:
        repositories.insert("material_chunks", {
            "material_id": record["id"],
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
        record["id"],
        title=record["name"],
        raw_text=raw_text,
        structured={
            "chunk_count": len(chunks),
            "embedding_backend": embedding_backend(),
            **(extra_structured or {}),
        },
        summary=f"{len(chunks)} chunks indexed for retrieval.",
    )
    saved = repositories.update("materials", record["id"], {
        "raw_text": raw_text,
        "markdown_path": markdown_path,
        "chunk_count": len(chunks),
        "embedding_status": "ready" if chunks else "empty",
        "processing_error": "",
    }) or record
    return saved


def list_materials() -> list[MaterialResponse]:
    records = repositories.list_all("materials")
    return [MaterialResponse(**r) for r in records]


def get_material(material_id: str) -> MaterialResponse | None:
    record = repositories.get("materials", material_id)
    if record is None:
        return None
    return MaterialResponse(**record)
