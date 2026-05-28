import asyncio
import logging
from dataclasses import dataclass

from api.db import repositories
from api.services import material_service

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MaterialJob:
    material_id: str


_queue: asyncio.Queue[MaterialJob] | None = None
_worker_task: asyncio.Task | None = None
_queued_ids: set[str] = set()
_active_id: str | None = None


def start_material_queue() -> None:
    global _queue, _worker_task
    if _queue is None:
        _queue = asyncio.Queue()
    if _worker_task is None or _worker_task.done():
        _worker_task = asyncio.create_task(_worker_loop())


async def stop_material_queue() -> None:
    global _worker_task
    if _worker_task is None:
        return
    _worker_task.cancel()
    try:
        await _worker_task
    except asyncio.CancelledError:
        pass
    _worker_task = None


async def enqueue_material_processing(material_id: str) -> None:
    global _queue
    if _queue is None:
        start_material_queue()
    assert _queue is not None

    if material_id == _active_id or material_id in _queued_ids:
        return

    record = repositories.get("materials", material_id)
    if record:
        repositories.update("materials", material_id, {
            "embedding_status": "queued",
            "processing_error": "",
        })

    _queued_ids.add(material_id)
    await _queue.put(MaterialJob(material_id=material_id))


def queue_snapshot() -> dict:
    size = _queue.qsize() if _queue is not None else 0
    return {
        "active_material_id": _active_id,
        "queued_count": size,
        "queued_material_ids": list(_queued_ids),
    }


async def _worker_loop() -> None:
    global _active_id
    assert _queue is not None
    while True:
        job = await _queue.get()
        _queued_ids.discard(job.material_id)
        _active_id = job.material_id
        try:
            await asyncio.to_thread(material_service.process_pdf_material, job.material_id)
        except Exception:
            logger.exception("Material processing job failed: material_id=%s", job.material_id)
        finally:
            _active_id = None
            _queue.task_done()
