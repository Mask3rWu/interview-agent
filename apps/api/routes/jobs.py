from fastapi import APIRouter, HTTPException
from api.schemas.job import JobCreate, JobResponse
from api.services import job_service

router = APIRouter()


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(body: JobCreate):
    return job_service.create_job(body)


@router.get("", response_model=list[JobResponse])
async def list_jobs():
    return job_service.list_jobs()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    result = job_service.get_job(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return result
