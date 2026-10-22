"""
OCR Service for Notice Saathi.
Extracts verbatim text from images (JPG, PNG) and PDFs using Gemini Vision (google-genai SDK).
Currently focused on English document text extraction.
"""

import logging
import os
import time
from fastapi import HTTPException, status
from google import genai
from google.genai import types

logger = logging.getLogger("notice_saathi.ocr")

OCR_PROMPT = (
    "Extract all text from this English document exactly as written. "
    "Preserve line breaks, reading order, and document layout as closely as possible. "
    "Do NOT summarize, do NOT translate, do NOT explain, and do NOT correct spelling or grammar. "
    "Output only the raw extracted text verbatim, with no introductory text or markdown formatting code blocks."
)


class OCRService:
    def __init__(self):
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        """Lazy initialization of Gemini client without import-time network calls or key checks."""
        if self._client is not None:
            return self._client

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or not api_key.strip():
            logger.error("GEMINI_API_KEY is not configured in backend environment")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OCR service is not configured. Please set GEMINI_API_KEY in backend/.env.",
            )

        try:
            self._client = genai.Client(api_key=api_key.strip())
            return self._client
        except Exception as e:
            logger.exception(f"Failed to initialize Gemini client: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not initialize the document reading service. Please try again later.",
            )

    def _extract_with_gemini(self, file_bytes: bytes, mime_type: str) -> str:
        """Send image or PDF bytes directly to Gemini Vision to extract raw text."""
        client = self._get_client()
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

        part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)

        max_attempts = 3
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    f"Extracting text with Gemini Vision ({model_name}) | Mime: {mime_type} | Attempt: {attempt}/{max_attempts}"
                )
                response = client.models.generate_content(
                    model=model_name,
                    contents=[part, OCR_PROMPT],
                )

                text = (response.text or "").strip()
                if text:
                    return text

                # Check candidate parts if text accessor is empty
                if response.candidates:
                    first_cand = response.candidates[0]
                    if first_cand.content and first_cand.content.parts:
                        parts_text = "".join(
                            getattr(p, "text", "") or "" for p in first_cand.content.parts
                        ).strip()
                        if parts_text:
                            return parts_text

                logger.warning(f"Gemini returned empty text on attempt {attempt}/{max_attempts}")
                last_error = "Empty text response from Gemini"

            except HTTPException:
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"Gemini Vision request failed on attempt {attempt}/{max_attempts}: {e}")
                if attempt < max_attempts:
                    time.sleep(attempt * 1.5)

        logger.error(f"Gemini Vision OCR extraction failed completely: {last_error}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not read the document, please try again with a clearer photo or PDF.",
        )

    def _ocr_image_bytes(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
        """Compatibility helper for processing image bytes."""
        return self._extract_with_gemini(image_bytes, mime_type)

    def _ocr_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """Compatibility helper for processing PDF bytes."""
        return self._extract_with_gemini(pdf_bytes, "application/pdf")

    def extract_text(self, file_bytes: bytes, content_type: str) -> str:
        """
        Extract text from file bytes based on content_type (image/jpeg, image/png, application/pdf).
        Returns the combined text string or raises HTTPException if extraction fails.
        """
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )

        normalized_type = content_type.lower()
        if normalized_type == "image/jpg":
            normalized_type = "image/jpeg"

        if normalized_type not in ("image/jpeg", "image/png", "application/pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported content type: '{content_type}'. Must be image/jpeg, image/png, or application/pdf.",
            )

        extracted_text = self._extract_with_gemini(file_bytes, normalized_type)

        if not extracted_text or not extracted_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No readable text could be detected in the uploaded notice.",
            )

        return extracted_text.strip()


# Global singleton instance for injection into routes
ocr_service = OCRService()
