import io
import logging
import time
from typing import Literal
from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException, status
from fastapi.responses import Response, StreamingResponse, JSONResponse

try:
    from backend.models.notice import AnalyzeResponse, NoticeData, ExplanationPoint, ReexplainRequest
    from backend.services.ocr_service import ocr_service
    from backend.services.agent_service import agent_service
    from backend.services.voice_service import voice_service
    from backend.services.reminder_service import reminder_service
except ModuleNotFoundError:
    from models.notice import AnalyzeResponse, NoticeData, ExplanationPoint, ReexplainRequest
    from services.ocr_service import ocr_service
    from services.agent_service import agent_service
    from services.voice_service import voice_service
    from services.reminder_service import reminder_service

logger = logging.getLogger("notice_saathi.routes")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

router = APIRouter(tags=["notice"])

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_SPEAK_TEXT_LENGTH = 2000
MIN_OCR_TEXT_LENGTH = 20


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_notice(
    file: UploadFile = File(..., description="Uploaded notice image or PDF (max 10MB)"),
    language: str = Form("en", description="Target language ('en' or 'hi')"),
):
    """
    Analyze uploaded notice document with full error resilience and execution logging.
    1. Validates file format and size
    2. Runs OCR (Google Cloud Vision)
    3. Guards against blurry/empty text (<20 characters)
    4. Runs AI agent reasoning (Anthropic Claude with 30s timeout)
    Always returns structured JSON matching AnalyzeResponse, never raw 500 HTML.
    """
    start_time = time.perf_counter()
    filename = file.filename or "uploaded_document"
    logger.info(f"[/analyze] New request | File: '{filename}' | Reported Type: '{file.content_type}' | Target Lang: '{language}'")

    try:
        # 1. Validate Content Type
        content_type = (file.content_type or "").lower()
        if content_type == "image/jpg":
            content_type = "image/jpeg"

        if content_type not in ALLOWED_CONTENT_TYPES:
            fname_lower = filename.lower()
            if fname_lower.endswith((".jpg", ".jpeg")):
                content_type = "image/jpeg"
            elif fname_lower.endswith(".png"):
                content_type = "image/png"
            elif fname_lower.endswith(".pdf"):
                content_type = "application/pdf"
            else:
                logger.warning(f"[/analyze] Rejected unsupported file format: '{file.content_type}' for '{filename}'")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "status": "error",
                        "message": "Only JPG, PNG and PDF files are supported. Please upload an image or PDF document.",
                        "data": None,
                    },
                )

        # 2. Read and validate file size (< 10MB)
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            logger.warning(f"[/analyze] Rejected empty file (0 bytes): '{filename}'")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": "The uploaded file is empty. Please select a valid document.",
                    "data": None,
                },
            )

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            size_mb = len(file_bytes) / (1024 * 1024)
            logger.warning(f"[/analyze] Rejected oversized file ({size_mb:.2f} MB): '{filename}'")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": f"That file is larger than 10 MB ({size_mb:.1f} MB). Please compress or crop your file.",
                    "data": None,
                },
            )

        # 3. Extract text via OCR service
        ocr_start = time.perf_counter()
        extracted_text = ocr_service.extract_text(file_bytes=file_bytes, content_type=content_type)
        ocr_duration = time.perf_counter() - ocr_start

        clean_text = extracted_text.strip()
        logger.info(f"[/analyze] OCR finished in {ocr_duration:.2f}s | Extracted {len(clean_text)} characters")

        # 4. Short text guard (< 20 characters)
        if len(clean_text) < MIN_OCR_TEXT_LENGTH:
            logger.warning(
                f"[/analyze] Extracted text too short ({len(clean_text)} chars): '{clean_text}'. Skipping AI agent."
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "status": "error",
                    "message": "We couldn't read that notice. Please try again with a clearer photo or a PDF.",
                    "data": None,
                },
            )

        # 5. Run AI Agent analysis (Claude with 30s timeout)
        ai_start = time.perf_counter()
        normalized_lang: Literal["en", "hi"] = "hi" if language.lower() == "hi" else "en"
        notice_data = await agent_service.analyze_notice(
            raw_text=extracted_text,
            language=normalized_lang,
        )
        ai_duration = time.perf_counter() - ai_start
        total_duration = time.perf_counter() - start_time

        logger.info(
            f"[/analyze] SUCCESS in {total_duration:.2f}s (OCR: {ocr_duration:.2f}s, AI: {ai_duration:.2f}s) | "
            f"Type: '{notice_data.notice_type}' | Urgency: '{notice_data.urgency_level}' | Scam: '{notice_data.scam_likelihood}'"
        )

        return AnalyzeResponse(
            status="success",
            data=notice_data,
            message="Notice analysis completed successfully.",
        )

    except HTTPException as e:
        total_duration = time.perf_counter() - start_time
        logger.error(f"[/analyze] FAILED after {total_duration:.2f}s [HTTP {e.status_code}]: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={
                "status": "error",
                "message": str(e.detail),
                "data": None,
            },
        )
    except Exception as e:
        total_duration = time.perf_counter() - start_time
        logger.exception(f"[/analyze] UNHANDLED EXCEPTION after {total_duration:.2f}s: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "We couldn't process this notice right now. Please try again with a clearer photo or PDF.",
                "data": None,
            },
        )


@router.post("/reexplain", response_model=AnalyzeResponse)
async def reexplain_notice(payload: ReexplainRequest):
    """
    Re-explain notice in an alternate language (en/hi) without re-uploading the file.
    """
    start_time = time.perf_counter()
    logger.info(f"[/reexplain] New request | Target Lang: '{payload.language}' | Text Length: {len(payload.raw_text)}")

    try:
        notice_data = await agent_service.reexplain_notice(
            raw_text=payload.raw_text,
            language=payload.language,
        )
        total_duration = time.perf_counter() - start_time
        logger.info(f"[/reexplain] SUCCESS in {total_duration:.2f}s | Type: '{notice_data.notice_type}'")
        return AnalyzeResponse(
            status="success",
            data=notice_data,
            message=f"Notice successfully re-explained in {payload.language}.",
        )
    except HTTPException as e:
        total_duration = time.perf_counter() - start_time
        logger.error(f"[/reexplain] FAILED after {total_duration:.2f}s [HTTP {e.status_code}]: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={
                "status": "error",
                "message": str(e.detail),
                "data": None,
            },
        )
    except Exception as e:
        total_duration = time.perf_counter() - start_time
        logger.exception(f"[/reexplain] UNHANDLED EXCEPTION after {total_duration:.2f}s: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Failed to re-explain the notice. Please try again.",
                "data": None,
            },
        )


@router.get("/speak")
async def speak_text(
    text: str = Query(..., description="Text to synthesize to speech"),
    language: str = Query("en", description="Language code ('en' or 'hi')"),
):
    """
    Stream audio (MP3) for text-to-speech using gTTS.
    Directly compatible with frontend HTML5 <audio> element.
    """
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text parameter cannot be empty.",
        )

    if len(text) > MAX_SPEAK_TEXT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Text length exceeds {MAX_SPEAK_TEXT_LENGTH} characters limit "
                f"(received {len(text)} characters)."
            ),
        )

    audio_bytes = voice_service.generate_speech(text=text, language=language)

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=speech.mp3",
            "Content-Length": str(len(audio_bytes)),
        },
    )


@router.get("/reminder.ics")
async def get_reminder_calendar(
    title: str = Query(..., description="Event title"),
    deadline: str = Query(..., description="Deadline text or date"),
    language: str = Query("en", description="Language code ('en' or 'hi')"),
):
    """
    Download an iCalendar (.ics) attachment file for the notice deadline.
    """
    ics_bytes = reminder_service.generate_ics(
        title=title,
        deadline=deadline,
        language=language,
    )

    return Response(
        content=ics_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="reminder.ics"'},
    )
