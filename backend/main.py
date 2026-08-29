import os
import uuid

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Critical Error: Missing Supabase Environment Credentials inside .env"
    )


app = FastAPI(
    title=" AcciSense API",
    description="Distributed Traffic Accident Emergency Response & Escalation Gateway System",
    version="1.0.0"
)


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


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


# ==========================================
# CREATE INCIDENT
# ==========================================

@app.post("/incident")
async def create_incident(incident: IncidentCreateRequest):

    incident_id = f"AC-{uuid.uuid4().hex[:8].upper()}"

    return {
        "incident_id": incident_id,
        "incident_type": incident.incident_type,
        "location": incident.location,
        "severity_indicator": incident.severity_indicator,
        "status": "OPEN",
        "created_at": datetime.utcnow().isoformat()
    }


@app.post("/incident/{incident_id}/acknowledge")
async def acknowledge_incident(incident_id: str):
    """
    Acknowledge an AcciSense incident.

    Updates the corresponding record in the cards table
    using the AcciSense incident ID.
    """

    try:
        acknowledged_at = datetime.utcnow().isoformat()

        response = (
            supabase
            .table("cards")
            .update({
                "status": "Acknowledged",
                "acknowledged_at": acknowledged_at
            })
            .eq("acci_id", incident_id)
            .execute()
        )

        # No matching incident found
        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Incident {incident_id} not found"
            )

        return {
            "incident_id": incident_id,
            "status": "Acknowledged",
            "acknowledged_at": acknowledged_at
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to acknowledge incident: {str(e)}"
        )

# ==========================================
# GET CARDS
# ==========================================

@app.get(
    "/cards",
    response_model=List[IncidentCardResponse],
    status_code=status.HTTP_200_OK
)
async def get_cards():

    try:
        response = supabase.table("cards").select("*").execute()
        return response.data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database Retrieval Anomaly: {str(e)}"
        )


# ==========================================
# ROOT
# ==========================================

@app.get("/", status_code=status.HTTP_200_OK, include_in_schema=False)
async def root_diagnostic():

    return {
        "system_status": "ONLINE",
        "service": "AcciSense Core Gateway Engine"
    }