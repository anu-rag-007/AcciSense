import os
import requests
import uuid
from typing import Tuple
from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

from image_analysis import analyze_accident_image

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Critical Error: Missing Supabase Environment Credentials inside .env")


app = FastAPI(title=" AcciSense API", description="Distributed Traffic Accident Emergency Response & Escalation Gateway System",version="1.0.0")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


def classify_severity_ai(incident_type: str, description: str) -> Tuple[str, str]:
    text = f"{incident_type} {description}".lower()
    critical_keywords = ['fire', 'explosion', 'multiple casualties', 'trapped', 'fatal']
    high_keywords = ['injured', 'bleeding', 'collision', 'overturned']
    
    if any(keyword in text for keyword in critical_keywords):
        return "CRITICAL", "P0"
    elif any(keyword in text for keyword in high_keywords):
        return "HIGH", "P1"
    return "MEDIUM", "P2"


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IncidentCardResponse(BaseModel):
    card_id: str = Field(..., example="AC-B84061CB")
    location: str
    severity: str
    status: str
    created_at: datetime
    ipfs_audit_hash: Optional[str] = None


class IncidentCreateRequest(BaseModel):
    incident_type: str
    location: str
    severity_indicator: str

    description: Optional[str] = None
    severity_score: Optional[float] = None
    people_affected: Optional[int] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    event_time: Optional[str] = None
    ai_confidence: Optional[float] = None
    
    
@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    try:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400,detail="Please upload a valid image file.")

        image_bytes = await file.read()

        if not image_bytes:
            raise HTTPException(status_code=400,detail="Uploaded image is empty.")

        analysis = analyze_accident_image(image_bytes=image_bytes,mime_type=file.content_type)

        return {"filename": file.filename,"analysis": analysis}

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Image analysis failed: {str(e)}")
    
    
@app.post("/incident/from-image")
async def create_incident_from_image(file: UploadFile = File(...)):
    try:
        # Validate image
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="Please upload a valid image file."
            )

        image_bytes = await file.read()

        if not image_bytes:
            raise HTTPException(status_code=400,detail="Uploaded image is empty.")

        analysis = analyze_accident_image(image_bytes=image_bytes,mime_type=file.content_type)
        incident_type = analysis.get("incident_type","ACCIDENT_DETECTED")
        severity = analysis.get("severity","MEDIUM")
        severity_score = analysis.get("severity_score",50)
        priority = analysis.get("priority","P2")
        people_affected = analysis.get("people_affected")
        description = analysis.get("description","")
        ai_confidence = analysis.get("ai_confidence")
        incident_id = f"AC-{uuid.uuid4().hex[:8].upper()}"
        created_at = datetime.utcnow().isoformat()

        response = supabase.table("cards").insert({
            "acci_id": incident_id,
            "incident_type": incident_type,
            "location": "Location Pending",
            "severity": severity,
            "severity_score": severity_score,
            "priority": priority,
            "people_affected": people_affected,
            "ai_confidence": ai_confidence,
            "description": description,
            "status": "WAITING_FOR_ACK",
            "created_at": created_at
        }).execute()

        if not response.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create incident in Supabase."
            )
            
        n8n_payload = {
            "acci_id": incident_id,
            "priority": priority,
            "status": "UNACKNOWLEDGED",
            "severity_score": severity_score,
            "location": "Location Pending",
            "event": incident_type,

            "incident_type": incident_type,
            "severity": severity,
            "people_affected": people_affected,
            "description": description,
            "ai_confidence": ai_confidence
        }

        try:
            n8n_response = requests.post(
                "https://cherisher-bring-sedative.ngrok-free.dev/webhook/accisense-alert",
                json=n8n_payload,
                timeout=10
            )

            n8n_triggered = n8n_response.ok

        except requests.RequestException:
            n8n_triggered = False
            
        return {
            "incident_id": incident_id,
            "analysis": { "incident_type": incident_type, "severity": severity, "severity_score": severity_score,
            "priority": priority, "people_affected": people_affected, "description": description, "ai_confidence": ai_confidence
            },
            "location": "Location Pending",
            "status": "WAITING_FOR_ACK",
            "created_at": created_at,
            "n8n_triggered": n8n_triggered
        }

        return {
            "incident_id": incident_id,
            "analysis": {
                "incident_type": incident_type,
                "severity": severity,
                "severity_score": severity_score,
                "priority": priority,
                "people_affected": people_affected,
                "description": description,
                "ai_confidence": ai_confidence
            },
            "location": "Location Pending",
            "status": "WAITING_FOR_ACK",
            "created_at": created_at
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Image incident creation failed: {str(e)}")
    
    
@app.get("/incident/{incident_id}")
def get_incident(incident_id: str):
    result = (
        supabase
        .table("cards")
        .select("*")
        .eq("acci_id", incident_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    return result.data[0]
    if not result.data:
        raise HTTPException(status_code=404,detail="Incident not found")

    return result.data
    

@app.post("/incident")
async def create_incident(incident: IncidentCreateRequest):
    incident_id = f"AC-{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.utcnow().isoformat()

    ai_severity, priority = classify_severity_ai(incident.incident_type,incident.location)
    try:
        response = supabase.table("cards").insert({
            "acci_id": incident_id,
            "incident_type": incident.incident_type,
            "location": incident.location,
            "severity": incident.severity_indicator,
            "severity_score": incident.severity_score,
            "priority": priority,
            "people_affected": incident.people_affected,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
            "event_time": incident.event_time,
            "ai_confidence": incident.ai_confidence,
            "description": incident.description,
            "status": "WAITING_FOR_ACK",
            "created_at": created_at
        }).execute()

        return {
            "incident_id": incident_id,
            "incident_type": incident.incident_type,
            "location": incident.location,
            "severity": ai_severity,
            "priority": priority,
            "severity_score": incident.severity_score,
            "people_affected": incident.people_affected,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
            "event_time": incident.event_time,
            "ai_confidence": incident.ai_confidence,
           "description": incident.description,
           "status": "WAITING_FOR_ACK",
           "created_at": created_at
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Supabase insert failed: {str(e)}"
        )

@app.post("/incident/{incident_id}/acknowledge")
async def acknowledge_incident(incident_id: str):
    try:
        acknowledged_at = datetime.utcnow().isoformat()
        response = (supabase.table("cards").update({
                "status": "Acknowledged",
                "acknowledged_at": acknowledged_at
            }).eq("acci_id", incident_id).execute()
        )

        if not response.data:
            raise HTTPException(status_code=404,detail=f"Incident {incident_id} not found")

        return {"incident_id": incident_id,"status": "Acknowledged","acknowledged_at": acknowledged_at}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Failed to acknowledge incident: {str(e)}")
        
        
@app.post("/incident/{incident_id}/escalate")
async def escalate_incident(incident_id: str):
    try:
        current = (supabase
            .table("cards")
            .select("acci_id, status")
            .eq("acci_id", incident_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute())

        if not current.data:
            raise HTTPException(status_code=404,detail=f"Incident {incident_id} not found")

        current_status = current.data[0]["status"]
        if current_status == "ACKNOWLEDGED":
            return {
                "incident_id": incident_id,
                "status": "ACKNOWLEDGED",
                "escalated": False,
                "message": "Incident already acknowledged. Escalation cancelled."
            }

        # Only escalate if still unacknowledged
        escalated_at = datetime.utcnow().isoformat()

        response = (
            supabase
            .table("cards")
            .update({"status": "ESCALATED","escalated_at": escalated_at})
            .eq("acci_id", incident_id)
            .neq("status", "ACKNOWLEDGED")
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=409,detail=f"Incident {incident_id} was already acknowledged")

        return {"incident_id": incident_id,"status": "ESCALATED","escalated_at": escalated_at}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Escalation failed: {str(e)}")
        

@app.get("/cards",response_model=List[IncidentCardResponse],status_code=status.HTTP_200_OK)
async def get_cards():
    try:
        response = supabase.table("cards").select("*").execute()
        return response.data

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Database Retrieval Anomaly: {str(e)}")


@app.get("/", status_code=status.HTTP_200_OK, include_in_schema=False)
async def root_diagnostic():
    return {"system_status": "ONLINE","service": "AcciSense Core Gateway Engine"}