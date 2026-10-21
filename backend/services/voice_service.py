"""Voice Service for Text-to-Speech conversion using gTTS."""

import io
from typing import Literal
from fastapi import HTTPException, status
from gtts import gTTS
from gtts.tts import gTTSError


class VoiceService:
    def __init__(self):
        pass

    def generate_speech(self, text: str, language: str = "en") -> bytes:
        """
        Convert text to MP3 audio bytes using gTTS.
        Supports 'en' (English) and 'hi' (Hindi).
        Returns audio bytes in memory without writing to disk.
        """
        if not text or not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text for speech synthesis cannot be empty.",
            )

        # Normalize language
        lang_code = "hi" if language.lower() == "hi" else "en"

        try:
            fp = io.BytesIO()
            tts = gTTS(text=text.strip(), lang=lang_code, slow=False)
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.getvalue()
        except gTTSError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Text-to-speech synthesis error: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to generate speech audio: {str(e)}",
            )


# Global singleton instance
voice_service = VoiceService()
