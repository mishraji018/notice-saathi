# Notice Saathi — Backend API (FastAPI)

FastAPI backend service powering OCR extraction (Google Cloud Vision), legal document analysis & scam detection (Anthropic Claude), text-to-speech (gTTS), and calendar reminders (iCalendar).

---

## Environment Variables

Configure these environment variables in your deployment environment (Render, Railway, Fly.io, or `.env` locally):

| Variable | Required | Description | Example |
| :--- | :--- | :--- | :--- |
| `ANTHROPIC_API_KEY` | **Yes** | Anthropic API key for Claude model inference | `sk-ant-api03-...` |
| `GOOGLE_CREDENTIALS_BASE64` | **Yes** (or file) | Base64-encoded Google Cloud service account JSON | *See Base64 instructions below* |
| `GOOGLE_APPLICATION_CREDENTIALS` | Local only | File path to service account JSON (alternative to base64) | `/etc/secrets/gcp-key.json` |
| `ALLOWED_ORIGINS` | Recommended | Comma-separated CORS allowed origins | `https://notice-saathi.vercel.app,http://localhost:3000` |
| `PORT` | Auto-set | Port assigned dynamically by the host platform | `8000` |
| `POPPLER_PATH` | Optional | Custom directory for Poppler binaries (Windows only) | `C:\Program Files\poppler\Library\bin` |

---

## Google Cloud Credentials for Cloud Hosting (Base64 Method)

Hosting platforms like Render and Railway do not allow direct file uploads into runtime containers. Instead, encode your service account JSON file into a single Base64 string and set it as `GOOGLE_CREDENTIALS_BASE64`.

### How to Generate the Base64 String:

#### On Windows (PowerShell):
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\service-account-key.json")) | Set-Clipboard
```
*(The base64 string is now copied to your clipboard — paste it as the value of `GOOGLE_CREDENTIALS_BASE64` on your hosting platform dashboard).*

#### On macOS / Linux:
```bash
base64 -w 0 path/to/service-account-key.json
# or on macOS:
base64 -i path/to/service-account-key.json | pbcopy
```

The backend automatically detects and decodes `GOOGLE_CREDENTIALS_BASE64` at runtime.

---

## Start Commands

- **Render / Railway (Procfile)**:
  ```bash
  web: uvicorn main:app --host 0.0.0.0 --port $PORT
  ```
- **Manual Start**:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8000
  ```
- **Docker**:
  ```bash
  docker build -t notice-saathi-backend .
  docker run -p 8000:8000 --env-file .env notice-saathi-backend
  ```
