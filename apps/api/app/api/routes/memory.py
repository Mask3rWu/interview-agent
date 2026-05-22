from fastapi import APIRouter, Query
from app.services import memory_service

router = APIRouter()


@router.get("")
async def list_memories(sort_by: str = Query(default="mastery_score",
    description="Sort field: mastery_score, exposure_count, last_tested_at, weakness_count")):
    return memory_service.list_memories(sort_by=sort_by)


@router.post("/rebuild")
def rebuild_memories():
    return memory_service.rebuild_memories_from_interviews()
