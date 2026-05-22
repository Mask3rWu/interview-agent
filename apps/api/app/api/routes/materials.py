from fastapi import APIRouter, HTTPException
from app.schemas.material import MaterialCreate, MaterialResponse
from app.services import material_service

router = APIRouter()


@router.post("", response_model=MaterialResponse, status_code=201)
async def create_material(body: MaterialCreate):
    return material_service.create_material(body)


@router.get("", response_model=list[MaterialResponse])
async def list_materials():
    return material_service.list_materials()


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(material_id: str):
    result = material_service.get_material(material_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Material not found")
    return result
