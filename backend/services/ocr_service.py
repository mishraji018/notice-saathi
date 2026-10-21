"""
OCR Service for Notice Saathi.
Extracts text from images (JPG, PNG) and PDFs using Google Cloud Vision API.

Setup Note:
- To use Google Cloud Vision, download a Service Account JSON key from Google Cloud Console:
  (Console -> IAM & Admin -> Service Accounts -> Select/Create Account -> Keys -> Add Key -> JSON).
- Set GOOGLE_APPLICATION_CREDENTIALS in backend/.env to the absolute path of that JSON key file.
  Example: GOOGLE_APPLICATION_CREDENTIALS="C:\\Users\\pmish\\keys\\gcp-vision-key.json"
"""

import base64
import io
import json
import os
from typing import List
from fastapi import HTTPException, status
from google.cloud import vision
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2 import service_account
from pdf2image import convert_from_bytes
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError


class OCRService:
    def __init__(self):
        self._client: vision.ImageAnnotatorClient | None = None

    def _get_client(self) -> vision.ImageAnnotatorClient:
        """Lazy initialization of Google Cloud Vision client with clear error messages."""
        if self._client is not None:
            return self._client

        # 1. Check for Base64-encoded Service Account JSON (ideal for Render/Railway/Heroku)
        base64_creds = os.getenv("GOOGLE_CREDENTIALS_BASE64")
        if base64_creds and base64_creds.strip():
            try:
                decoded_bytes = base64.b64decode(base64_creds.strip())
                creds_info = json.loads(decoded_bytes.decode("utf-8"))
                credentials = service_account.Credentials.from_service_account_info(creds_info)
                self._client = vision.ImageAnnotatorClient(credentials=credentials)
                return self._client
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load GOOGLE_CREDENTIALS_BASE64: {str(e)}",
                )

        # 2. Check for raw JSON string in environment variable
        raw_json = os.getenv("GOOGLE_CREDENTIALS_JSON") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if raw_json and raw_json.strip():
            try:
                creds_info = json.loads(raw_json.strip())
                credentials = service_account.Credentials.from_service_account_info(creds_info)
                self._client = vision.ImageAnnotatorClient(credentials=credentials)
                return self._client
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load GOOGLE_CREDENTIALS_JSON: {str(e)}",
                )

        # 3. Check for file path via GOOGLE_APPLICATION_CREDENTIALS
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and not os.path.isabs(cred_path):
            cred_path = os.path.abspath(cred_path)

        if cred_path and not os.path.exists(cred_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"GOOGLE_APPLICATION_CREDENTIALS file not found at: '{cred_path}'. "
                    "Please verify the path in backend/.env, or use GOOGLE_CREDENTIALS_BASE64."
                ),
            )

        # 4. Standard default credentials resolution (ADC or file path)
        try:
            self._client = vision.ImageAnnotatorClient()
            return self._client
        except DefaultCredentialsError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Google Cloud credentials not found. Please set GOOGLE_CREDENTIALS_BASE64 "
                    "or GOOGLE_APPLICATION_CREDENTIALS in backend/.env."
                ),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize Google Cloud Vision client: {str(e)}",
            )

    def _ocr_image_bytes(self, image_bytes: bytes) -> str:
        """Run document text detection on single image bytes."""
        client = self._get_client()
        image = vision.Image(content=image_bytes)

        try:
            # document_text_detection is optimized for dense document text in English and Hindi/Devanagari
            response = client.document_text_detection(image=image)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Google Cloud Vision API request failed: {str(e)}",
            )

        if response.error.message:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Google Cloud Vision returned an error: {response.error.message}",
            )

        if response.full_text_annotation and response.full_text_annotation.text:
            return response.full_text_annotation.text.strip()

        return ""

    def _ocr_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """Convert PDF pages to images in memory and run document text detection on each page."""
        poppler_path = os.getenv("POPPLER_PATH")
        kwargs = {}
        if poppler_path and os.path.exists(poppler_path):
            kwargs["poppler_path"] = poppler_path

        try:
            pages = convert_from_bytes(pdf_bytes, **kwargs)
        except PDFInfoNotInstalledError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Poppler is required to process PDF files but was not found in PATH. "
                    "Install poppler (e.g. via `winget install OSGeo.Poppler` or `choco install poppler`) "
                    "or set POPPLER_PATH in backend/.env."
                ),
            )
        except (PDFPageCountError, PDFSyntaxError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or corrupted PDF file: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing PDF pages: {str(e)}",
            )

        if not pages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF contains no readable pages.",
            )

        extracted_pages: List[str] = []
        for i, page in enumerate(pages, start=1):
            buf = io.BytesIO()
            page.save(buf, format="PNG")
            page_text = self._ocr_image_bytes(buf.getvalue())
            if page_text:
                extracted_pages.append(f"--- Page {i} ---\n{page_text}")

        return "\n\n".join(extracted_pages).strip()

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
        if normalized_type in ("image/jpeg", "image/jpg", "image/png"):
            extracted_text = self._ocr_image_bytes(file_bytes)
        elif normalized_type == "application/pdf":
            extracted_text = self._ocr_pdf_bytes(file_bytes)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported content type: '{content_type}'. Must be image/jpeg, image/png, or application/pdf.",
            )

        if not extracted_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No readable text could be detected in the uploaded notice.",
            )

        return extracted_text


# Global singleton instance for injection into routes
ocr_service = OCRService()
