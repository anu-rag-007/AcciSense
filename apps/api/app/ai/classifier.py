import json
import logging
import time
from google import genai
from google.genai import types

from app.config import settings

log = logging.getLogger("accisense.ai")

# Module-level singleton client — one per process, not per request
_client = genai.Client(
    api_key=settings.gemini_api_key,
    http_options=types.HttpOptions(timeout=15_000),  # milliseconds
)

_MODEL_NAME = "gemini-flash-latest"

_PROMPT = """You are an emergency incident classifier for a 911-style dispatch system.

Look at the photo and classify the incident. Respond with ONLY valid JSON, no markdown:

{
  "category": "<one of: cardiac, stroke, trauma, fire, assault, minor_injury, vehicle_accident, fall, other>",
  "severity": "<one of: LOW, MEDIUM, HIGH, CRITICAL>",
  "confidence": <float 0.0-1.0>,
  "description": "<one short sentence, max 140 chars>"
}

Severity guide:
- CRITICAL: life-threatening now (unconscious, heavy bleeding, active fire, cardiac arrest)
- HIGH: serious but not immediately life-threatening (fractures, moderate bleeding)
- MEDIUM: needs attention (minor cuts, sprains, small fire contained)
- LOW: non-urgent (minor damage, no injury, reporting for record)

If the image is unclear, blurry, or unrelated to an emergency, set confidence < 0.4 and category "other"."""


def classify(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    Returns {category, severity, confidence, description}.
    Never raises — degrades to MEDIUM/other on any failure.
    """
    t0 = time.time()
    try:
        response = _client.models.generate_content(
            model=_MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                _PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        # New SDK honors response_mime_type — text is pure JSON
        parsed = json.loads(response.text)

        result = {
            "category": str(parsed.get("category", "other")),
            "severity": str(parsed.get("severity", "MEDIUM")).upper(),
            "confidence": float(parsed.get("confidence", 0.0)),
            "description": str(parsed.get("description", ""))[:200],
        }
        log.info("classify ok in %.2fs: %s", time.time() - t0, result)
        return result

    except Exception as e:
        log.warning("classify failed after %.2fs: %s: %s",
                    time.time() - t0, type(e).__name__, e, exc_info=True)
        return {
            "category": "other",
            "severity": "MEDIUM",
            "confidence": 0.0,
            "description": f"AI failed: {type(e).__name__}: {str(e)[:120]}",
        }