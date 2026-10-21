"""
Smoke Test for Notice Saathi Backend.
Tests all endpoints against http://localhost:8000:
1. GET /health
2. POST /analyze (multipart upload of sample_notice.jpg)
3. POST /reexplain (Hindi re-explanation)
4. GET /speak (Text-to-Speech audio streaming)
5. GET /reminder.ics (iCalendar event download)
"""

import sys
import os
import json
from pathlib import Path
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Find sample notice image path
SCRIPT_DIR = Path(__file__).resolve().parent
SAMPLE_IMAGE_CANDIDATES = [
    SCRIPT_DIR / "sample_notice.jpg",
    SCRIPT_DIR.parent / "backend" / "sample_notice.jpg",
    Path("backend/sample_notice.jpg"),
    Path("sample_notice.jpg"),
]

sample_image_path = None
for candidate in SAMPLE_IMAGE_CANDIDATES:
    if candidate.exists():
        sample_image_path = candidate
        break

print("=" * 60)
print(f"NOTICE SAATHI BACKEND SMOKE TEST")
print(f"Target URL: {BASE_URL}")
print("=" * 60)

passed_tests = 0
total_tests = 5
extracted_raw_text = None

# -------------------------------------------------------------
# TEST 1: GET /health
# -------------------------------------------------------------
print("\n[TEST 1] Testing GET /health...")
try:
    res = requests.get(f"{BASE_URL}/health", timeout=5)
    if res.status_code == 200 and res.json().get("status") == "ok":
        print(f"Response: {res.json()}")
        print("[PASS] GET /health returned 200 OK")
        passed_tests += 1
    else:
        print(f"[FAIL] GET /health returned {res.status_code}: {res.text}")
except Exception as e:
    print(f"[FAIL] Could not connect to {BASE_URL}: {e}")
    print("Please make sure the backend uvicorn server is running.")
    sys.exit(1)

# -------------------------------------------------------------
# TEST 2: POST /analyze
# -------------------------------------------------------------
print("\n[TEST 2] Testing POST /analyze (Image OCR + AI Analysis)...")
if not sample_image_path:
    print(f"[FAIL] Sample image not found! Please place an image at: {SCRIPT_DIR / 'sample_notice.jpg'}")
else:
    print(f"Using sample image: {sample_image_path}")
    try:
        with open(sample_image_path, "rb") as f:
            files = {"file": ("sample_notice.jpg", f, "image/jpeg")}
            data = {"language": "en"}
            res = requests.post(f"{BASE_URL}/analyze", files=files, data=data, timeout=60)

        try:
            res_json = res.json()
        except Exception:
            res_json = res.text

        print("Full JSON Response:")
        print(json.dumps(res_json, indent=2, ensure_ascii=False) if isinstance(res_json, dict) else res_json)

        if res.status_code == 200 and isinstance(res_json, dict) and res_json.get("status") == "success":
            print("[PASS] POST /analyze executed successfully")
            passed_tests += 1
            extracted_raw_text = res_json.get("data", {}).get("raw_text")
        else:
            print(f"[FAIL] POST /analyze returned status {res.status_code}")
            if isinstance(res_json, dict) and "detail" in res_json:
                print(f"Note: {res_json['detail']}")
    except Exception as e:
        print(f"[FAIL] POST /analyze request error: {e}")

# Fallback text if OCR step was skipped or failed due to missing cloud credentials
if not extracted_raw_text:
    extracted_raw_text = (
        "INCOME TAX DEPARTMENT\n"
        "Notice under section 142(1) of the Income Tax Act, 1961.\n"
        "Assessment Year 2024-25. Demand Amount: Rs 48,200. Deadline: 15 November 2026."
    )
    print(f"(Using sample notice text for subsequent tests)")

# -------------------------------------------------------------
# TEST 3: POST /reexplain
# -------------------------------------------------------------
print("\n[TEST 3] Testing POST /reexplain (Language: Hindi)...")
try:
    payload = {"raw_text": extracted_raw_text, "language": "hi"}
    res = requests.post(f"{BASE_URL}/reexplain", json=payload, timeout=60)
    try:
        res_json = res.json()
    except Exception:
        res_json = res.text

    print("Full JSON Response:")
    print(json.dumps(res_json, indent=2, ensure_ascii=False) if isinstance(res_json, dict) else res_json)

    if res.status_code == 200 and isinstance(res_json, dict) and res_json.get("status") == "success":
        print("[PASS] POST /reexplain executed successfully in Hindi")
        passed_tests += 1
    else:
        print(f"[FAIL] POST /reexplain returned status {res.status_code}")
except Exception as e:
    print(f"[FAIL] POST /reexplain request error: {e}")

# -------------------------------------------------------------
# TEST 4: GET /speak
# -------------------------------------------------------------
print("\n[TEST 4] Testing GET /speak (Text-to-Speech audio streaming)...")
try:
    params = {"text": "Your notice deadline is approaching. Please take action.", "language": "en"}
    res = requests.get(f"{BASE_URL}/speak", params=params, timeout=15)
    content_type = res.headers.get("content-type", "")
    content_len = len(res.content)

    print(f"Status Code: {res.status_code}")
    print(f"Content-Type: {content_type}")
    print(f"Audio Length: {content_len} bytes")

    if res.status_code == 200 and "audio/mpeg" in content_type and content_len > 1000:
        print("[PASS] GET /speak successfully returned audio/mpeg stream")
        passed_tests += 1
    else:
        print(f"[FAIL] GET /speak returned status {res.status_code} with {content_len} bytes")
except Exception as e:
    print(f"[FAIL] GET /speak request error: {e}")

# -------------------------------------------------------------
# TEST 5: GET /reminder.ics
# -------------------------------------------------------------
print("\n[TEST 5] Testing GET /reminder.ics (iCalendar event download)...")
try:
    params = {"title": "Income Tax Notice Deadline", "deadline": "15 Nov 2026", "language": "en"}
    res = requests.get(f"{BASE_URL}/reminder.ics", params=params, timeout=10)
    content_type = res.headers.get("content-type", "")

    print(f"Status Code: {res.status_code}")
    print(f"Content-Type: {content_type}")
    print("ICS Snippet:")
    print(res.text[:180])

    if res.status_code == 200 and "text/calendar" in content_type and "BEGIN:VCALENDAR" in res.text:
        print("[PASS] GET /reminder.ics successfully returned valid iCalendar file")
        passed_tests += 1
    else:
        print(f"[FAIL] GET /reminder.ics returned unexpected format (status {res.status_code})")
except Exception as e:
    print(f"[FAIL] GET /reminder.ics request error: {e}")

# -------------------------------------------------------------
# SUMMARY
# -------------------------------------------------------------
print("\n" + "=" * 60)
print(f"SMOKE TEST SUMMARY: {passed_tests}/{total_tests} Tests Passed")
print("=" * 60)
if passed_tests == total_tests:
    print("ALL TESTS PASSED! Backend is fully functional.")
else:
    print(f"{total_tests - passed_tests} test(s) encountered issues. Check logs above.")
