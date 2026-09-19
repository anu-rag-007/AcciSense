import hashlib
import uuid
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.supabase_client import supabase
from app.ai.classifier import classify

router = APIRouter(prefix="/incidents", tags=["incidents"])

BUCKET = "incident-media"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB


class ReportResponse(BaseModel):
    incident_id: str
    media_url: str
    content_hash: str
    severity: str | None = None
    category: str | None = None
    dispatch_status: str


@router.post("/realtime", response_model=ReportResponse)
def report_realtime(
    photo: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    captured_at: str = Form(...),
    description: str | None = Form(None),
    client_hash: str | None = Form(None),
):
    image_bytes = photo.file.read()

    if not image_bytes:
        raise HTTPException(400, "empty_photo")
    if len(image_bytes) > MAX_BYTES:
        raise HTTPException(413, "photo_too_large")

    server_hash = hashlib.sha256(image_bytes).hexdigest()

    # If the client sent a hash and it doesn't match, flag it (but don't reject
    # for now — trust is a Phase 2 concern).
    if client_hash and client_hash != server_hash:
        # Log it on the incident row later; for now just note in the response.
        pass

    ext = (photo.filename or "photo.jpg").rsplit(".", 1)[-1].lower()
    if ext not in {"jpg", "jpeg", "png", "webp", "heic"}:
        ext = "jpg"
    object_path = f"{uuid.uuid4()}.{ext}"

    try:
        supabase.storage.from_(BUCKET).upload(
            object_path,
            image_bytes,
            {"content-type": photo.content_type or "image/jpeg"},
        )
    except Exception as e:
        raise HTTPException(500, f"upload_failed: {e}")

    media_url = supabase.storage.from_(BUCKET).get_public_url(object_path)

        # ── Classify BEFORE insert so the row lands complete
    classification = classify(image_bytes, mime_type=photo.content_type or "image/jpeg")

    incident_insert = supabase.table("incidents").insert({
        "latitude": latitude,
        "longitude": longitude,
        "description": description or classification["description"],
        "category": classification["category"],
        "severity": classification["severity"],
        "ai_confidence": classification["confidence"],
        "dispatch_status": "reported",
    }).execute()

    if not incident_insert.data:
        raise HTTPException(500, "incident_insert_failed")

    incident = incident_insert.data[0]
    incident_id = incident["id"]

    supabase.table("incident_media").insert({
        "incident_id": incident_id,
        "storage_url": media_url,
        "content_hash": server_hash,
        "captured_at": captured_at,
        "gps_lat": latitude,
        "gps_lng": longitude,
    }).execute()

    return ReportResponse(
        incident_id=incident_id,
        media_url=media_url,
        content_hash=server_hash,
        severity=classification["severity"],
        category=classification["category"],
        dispatch_status=incident["dispatch_status"],
    )