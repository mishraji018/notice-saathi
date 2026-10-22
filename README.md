# Notice Saathi

Upload a government notice (photo or PDF) and get it explained in plain English or Hindi — what it means, what to do, key deadlines and amounts, and warning signs of a fake notice.

**Stack:** TanStack Start (React 19 + TypeScript) + Tailwind CSS v4.

## Features

- Upload a notice as JPG/PNG/PDF (up to 10 MB), by click or drag & drop
- Simplified explanation with source lines quoted from the notice
- Urgency badge, key facts grid (authority / deadline / amount)
- Scam warning banner with reasons
- "Listen" button (text-to-speech), calendar reminder download, official helpline link
- Full English/Hindi UI; switching language re-explains the notice without re-uploading
- Robust error handling: network offline detection, request timeouts (35s), and friendly failure states

## Quick Start

### 1. Backend Setup (FastAPI)

```sh
cd backend
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your GEMINI_API_KEY and GROQ_API_KEY

uvicorn main:app --reload --port 8000
```

The backend API will run on `http://localhost:8000` (docs available at `http://localhost:8000/docs`).

### 2. Frontend Setup (TanStack Start)

```sh
# In repository root
npm i
npm run dev
```

The web app will run on `http://localhost:5173` (or the port Vite prints).

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default / Example |
|---|---|---|
| `GEMINI_API_KEY` | Required for Gemini Vision OCR | `AIzaSy...` |
| `GEMINI_MODEL` | Gemini OCR model name | `gemini-2.5-flash` |
| `GROQ_API_KEY` | Primary LLM provider for analysis | `gsk_...` |
| `GROQ_MODEL` | Primary model on Groq | `openai/gpt-oss-120b` |
| `ANTHROPIC_API_KEY` | Optional fallback LLM provider | `sk-ant-...` |
| `PORT` | API server port | `8000` |
| `ALLOWED_ORIGINS` | Comma-separated CORS allowed origins | `http://localhost:3000,http://localhost:5173` |

### Frontend (`.env.local`)

| Variable | Description | Default |
|---|---|---|
| `VITE_API_BASE_URL` | Backend URL for client-side API calls | `http://localhost:8000` |
| `NEXT_PUBLIC_API_BASE_URL` | Fallback backend URL for server-side calls | `http://localhost:8000` |

## Backend API contract

The frontend expects a backend at `VITE_API_BASE_URL` (default `http://localhost:8000`).
If the backend is unreachable or encounters an error, the frontend displays an informative error card with retry capability.

### `POST /analyze`

Analyze an uploaded notice file.

- **Request:** `multipart/form-data` with fields
  - `file` — the notice image/PDF (jpg/png/pdf, ≤ 10 MB)
  - `language` — `"en"` or `"hi"`
- **Response:** `AnalyzeResponse` JSON:

```json
{
  "status": "success",
  "data": {
    "notice_type": "Income Tax Notice — Section 142(1)",
    "authority": "National e-Assessment Centre, Income Tax Department",
    "deadline": "15 November 2026",
    "amount": "₹48,200 (demand shown in the notice)",
    "action_required": "…",
    "urgency_level": "high",
    "scam_likelihood": "medium",
    "scam_reasons": ["…"],
    "explanation_points": [
      { "text": "…", "source_sentence": "…" }
    ],
    "raw_text": "…full extracted text of the notice…",
    "helpline": { "name": "Aaykar Sampark Kendra", "number": "1800-180-1961" },
    "is_high_risk": true
  }
}
```

- `urgency_level`: `"high" | "medium" | "low"`
- `scam_likelihood`: `"high" | "medium" | "low" | "none"`
- `deadline`, `amount`, `authority`, `helpline` may be `null`
- **Error:** `{ "status": "error", "message": "…" }` (HTTP 4xx/5xx also accepted)

### `POST /reexplain`

Re-explain previously extracted text in another language (used when the user switches language after viewing results).

- **Request:** JSON `{ "raw_text": "…", "language": "en" | "hi" }`
- **Response:** same `AnalyzeResponse` shape as `/analyze`

### `GET /speak`

- **Query:** `text` (URL-encoded), `language` (`en` | `hi`)
- **Response:** audio stream (`audio/mpeg` or similar) that the frontend plays.
- If this endpoint is unreachable, the frontend falls back to the browser's built-in speech synthesis.

### `GET /reminder.ics`

- **Query:** `title`, `deadline`, `language` (all URL-encoded)
- **Response:** `text/calendar` attachment (an .ics file the browser downloads).
- If this endpoint is unreachable, the frontend generates a simple .ics locally.

## Configuration

- `VITE_API_BASE_URL` or `NEXT_PUBLIC_API_BASE_URL` — backend base URL (optional; default `http://localhost:8000`)

---

## Deployment to Vercel

When deploying the frontend to **Vercel**:

1. Import your Git repository into Vercel.
2. In **Project Settings** -> **Environment Variables**, add:
   - `NEXT_PUBLIC_API_BASE_URL` = your live backend URL (e.g. `https://notice-saathi-api.onrender.com`)
   - `VITE_API_BASE_URL` = your live backend URL (e.g. `https://notice-saathi-api.onrender.com`)
3. Deploy / Redeploy.
4. Add your deployed Vercel domain (e.g. `https://your-project.vercel.app`) to `ALLOWED_ORIGINS` on your Render/Railway backend.
