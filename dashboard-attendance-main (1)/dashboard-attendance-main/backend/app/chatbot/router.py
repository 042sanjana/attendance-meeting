from fastapi import APIRouter, HTTPException, UploadFile, File
from tempfile import NamedTemporaryFile
import os

from app.chatbot.schemas import ChatRequest, ChatResponse
from app.chatbot.services.chat_service import chat
from app.chatbot.rag.ingestion import index_meetings


router = APIRouter(
    prefix="/api/chatbot",
    tags=["Workforce AI Chatbot"],
)


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    try:
        result = chat(
            message=payload.message,
            session_id=payload.session_id or "default",
        )

        return result

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Chatbot processing failed. "
                "Check the FastAPI terminal for the underlying error."
            ),
        ) from exc


@router.post("/reindex-meetings")
def reindex_meetings_endpoint():
    try:
        return index_meetings()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Meeting indexing failed: {exc}",
        ) from exc


@router.post("/audio/transcribe")
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    try:
        suffix = os.path.splitext(file.filename or "audio.webm")[1].lower() or ".webm"
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            temp_path = tmp.name

        try:
            from app.chatbot.audio.transcription import transcribe_wav

            result = transcribe_wav(temp_path)
            return {"filename": file.filename, **result}
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audio transcription failed: {exc}") from exc


@router.post("/audio/process")
async def process_audio_endpoint(file: UploadFile = File(...)):
    try:
        suffix = os.path.splitext(file.filename or "audio.webm")[1].lower() or ".webm"
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            temp_path = tmp.name

        try:
            from app.chatbot.audio.transcription import transcribe_wav
            from app.chatbot.audio.meeting_processor import process_transcript

            transcription = transcribe_wav(temp_path)
            transcript = transcription["transcript"]

            try:
                processed = process_transcript(transcript)
            except Exception:
                processed = {"summary": "", "decisions": [], "tasks": []}

            return {
                "filename": file.filename,
                "transcript": transcript,
                "language": transcription["language"],
                "duration": transcription["duration"],
                **processed,
            }
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audio meeting processing failed: {exc}") from exc
