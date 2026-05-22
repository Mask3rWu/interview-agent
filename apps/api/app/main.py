import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import API_HOST, API_PORT
from app.core.logging import setup_logging
from app.api.routes import resumes, jobs, materials, interviews, memory

setup_logging()

app = FastAPI(title="Interview Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(materials.router, prefix="/materials", tags=["materials"])
app.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
app.include_router(memory.router, prefix="/memory", tags=["memory"])


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=True)
