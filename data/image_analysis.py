import os
import json
import base64
import requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")


def analyze_accident_image(image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    prompt = """
You are an emergency accident-analysis AI.

Analyze the provided traffic accident image and return ONLY valid JSON.

Determine:

1. incident_type
2. severity: LOW, MEDIUM, HIGH, or CRITICAL
3. severity_score: integer from 0 to 100
4. priority:
   - CRITICAL -> P0
   - HIGH -> P1
   - MEDIUM -> P2
   - LOW -> P3
5. people_affected:
   - count only people clearly visible in the image
   - use null if the number cannot be reliably determined
6. description
7. ai_confidence: number between 0 and 1

Do NOT invent:
- GPS coordinates
- exact location
- exact event time
- hidden people
- facts that cannot be visually supported

Return exactly this structure:

{
  "incident_type": "...",
  "severity": "...",
  "severity_score": 0,
  "priority": "...",
  "people_affected": null,
  "description": "...",
  "ai_confidence": 0.0
}
"""

    url = ("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        f"?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt},{"inline_data": {"mime_type": mime_type,"data": image_base64}}]}],
        "generationConfig": {"temperature": 0.1,"responseMimeType": "application/json"}
    }

    response = requests.post(
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent",
    headers={"x-goog-api-key": GEMINI_API_KEY,
             "Content-Type": "application/json"},json=payload,timeout=60)
    response.raise_for_status()
    data = response.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    result = json.loads(text)
    
    return result