from fastapi import APIRouter, HTTPException
from app.schemas.resume import ResumeCreate, ResumeResponse
from app.services import resume_service

router = APIRouter()


@router.post("", response_model=ResumeResponse, status_code=201)
async def create_resume(body: ResumeCreate):
    return resume_service.create_resume(body)


@router.get("", response_model=list[ResumeResponse])
async def list_resumes():
    return resume_service.list_resumes()


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: str):
    result = resume_service.get_resume(resume_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return result
