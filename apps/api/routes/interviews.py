import json
import traceback
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from api.schemas.interview import InterviewCreate, AnswerRequest, InterviewEvent
from api.services import interview_service

router = APIRouter()


@router.get("")
async def list_interviews():
    return interview_service.list_sessions()


@router.post("", status_code=201)
async def create_interview(body: InterviewCreate):
    session = interview_service.create_session(body)
    event = await interview_service.generate_first_question(session)
    return {
        "session_id": session.id,
        "status": session.status,
        "first_question": event.data,
    }


@router.get("/{session_id}")
async def get_interview(session_id: str):
    session = interview_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/answer")
async def submit_answer(session_id: str, body: AnswerRequest):
    try:
        event = await interview_service.submit_answer(session_id, body.answer)
        if event.event == "error":
            raise HTTPException(status_code=400, detail=str(event.data))
        return event
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/finish")
async def finish_interview(session_id: str):
    event = await interview_service.finish_interview(session_id)
    if event.event == "error":
        raise HTTPException(status_code=400, detail=str(event.data))
    return event


@router.post("/{session_id}/assess")
async def reassess_interview(session_id: str):
    event = await interview_service.reassess_interview(session_id)
    if event.event == "error":
        raise HTTPException(status_code=400, detail=str(event.data))
    return event


@router.post("/{session_id}/answer/stream")
async def submit_answer_stream(session_id: str, body: AnswerRequest):
    """
    SSE streaming version of submit_answer.
    Streams the interviewer's question token by token (mock simulates this).
    """
    try:
        event = await interview_service.submit_answer(session_id, body.answer)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    if event.event == "error":
        raise HTTPException(status_code=400, detail=str(event.data))

    async def generate():
        if event.event == "assessment":
            yield f"event: assessment\ndata: {json.dumps(event.data, ensure_ascii=False)}\n\n"
        else:
            # Simulate token-by-token streaming
            text = event.data if isinstance(event.data, str) else ""
            for i in range(0, len(text), 3):
                chunk = text[i:i+3]
                yield f"event: token\ndata: {json.dumps({'token': chunk}, ensure_ascii=False)}\n\n"
            yield f"event: message_end\ndata: {json.dumps({'full_text': text}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
