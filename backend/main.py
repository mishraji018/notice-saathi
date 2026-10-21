import os
import sys
from pathlib import Path

# Add project root and backend dir to sys.path so app runs whether executed from root or backend/
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
for path in (str(ROOT_DIR), str(BACKEND_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.routes.notice import router as notice_router
except ModuleNotFoundError:
    from routes.notice import router as notice_router

load_dotenv()

app = FastAPI(
    title="Notice Saathi API",
    description="FastAPI backend for Notice Saathi - Notice analysis, OCR, voice synthesis, and calendar reminders.",
    version="0.1.0",
)

# Configure CORS via ALLOWED_ORIGINS environment variable (comma-separated)
# Default includes local Next.js and Vite dev servers
raw_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173")
allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if "*" not in allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}

# Notice routes
app.include_router(notice_router)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
