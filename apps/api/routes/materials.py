from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from api.schemas.material import MaterialCreate, MaterialResponse
from api.services import material_queue, material_service

router = APIRouter()


@router.post("", response_model=MaterialResponse, status_code=201)
async def create_material(body: MaterialCreate):
    return material_service.create_material(body)


@router.post("/upload", response_model=MaterialResponse, status_code=201)
async def upload_material(
    name: str = Form(...),
    file: UploadFile = File(...),
):
    try:
        material = await material_service.create_pdf_material(name, file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await material_queue.enqueue_material_processing(material.id)
    queued = material_service.get_material(material.id)
    return queued or material


@router.get("", response_model=list[MaterialResponse])
async def list_materials():
    return material_service.list_materials()


@router.get("/queue/status")
async def material_queue_status():
    return material_queue.queue_snapshot()


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(material_id: str):
    result = material_service.get_material(material_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Material not found")
    return result


@router.post("/{material_id}/reprocess", response_model=MaterialResponse)
async def reprocess_material(material_id: str):
    record = material_service.get_material(material_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Material not found")
    if record.type != "pdf" or not record.source_file_path:
        raise HTTPException(status_code=400, detail="Only uploaded PDF materials can be reprocessed")
    await material_queue.enqueue_material_processing(material_id)
    queued = material_service.get_material(material_id)
    return queued or record
