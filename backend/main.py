from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    IncidentRequest,
    IncidentResponse,
    AcknowledgementResponse
)

from analysis import analyze_incident

from datetime import datetime, timezone
import uuid
import asyncio


# ==================================================
# CONFIGURATION
# ==================================================

ESCALATION_TIMEOUT = 300


# ==================================================
# APP
# ==================================================

app = FastAPI(
    title="AcciSense API",
    description="Prototype backend for the AcciSense accident-response system",
    version="0.3.0"
)


# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# TEMPORARY INCIDENT STORAGE
# ==================================================

incidents = {}


# ==================================================
# HELPER
# ==================================================

def current_time():
    return datetime.now(timezone.utc).isoformat()


# ==================================================
# ESCALATION TIMER
# ==================================================

async def escalation_timer(incident_id: str):

    # Wait for the configured timeout
    await asyncio.sleep(ESCALATION_TIMEOUT)

    # Check whether incident still exists
    if incident_id not in incidents:
        return

    incident = incidents[incident_id]

    # If already acknowledged, do nothing
    if incident["status"] != "WAITING_FOR_ACK":
        return

    # No acknowledgement received
    incident["status"] = "ESCALATED"

    incident["escalated_at"] = current_time()

    print(
        f"[ESCALATION] "
        f"{incident_id} escalated because "
        f"no acknowledgement was received."
    )


# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/health")
def health_check():

    return {
        "status": "online",
        "service": "AcciSense Backend"
    }


# ==================================================
# CREATE INCIDENT
# ==================================================

@app.post(
    "/incident",
    response_model=IncidentResponse
)
async def create_incident(
    incident: IncidentRequest
):

    # Generate unique incident ID
    incident_id = (
        "AC-" +
        str(uuid.uuid4())[:8].upper()
    )

    # Analyze incident
    analysis = analyze_incident(
        incident.severity_indicator
    )

    # Store incident
    incident_data = {

        "incident_id": incident_id,

        "incident_type": incident.incident_type,

        "location": incident.location,

        "severity": analysis["severity"],

        "priority": analysis["priority"],

        "status": "WAITING_FOR_ACK",

        "created_at": current_time(),

        "acknowledged_at": None,

        "escalated_at": None
    }

    incidents[incident_id] = incident_data

    # Start escalation timer
    asyncio.create_task(
        escalation_timer(incident_id)
    )

    print(
        f"[NEW INCIDENT] {incident_id} "
        f"| {analysis['severity']} "
        f"| {analysis['priority']}"
    )

    return incident_data


# ==================================================
# GET INCIDENT
# ==================================================

@app.get(
    "/incident/{incident_id}",
    response_model=IncidentResponse
)
def get_incident(incident_id: str):

    if incident_id not in incidents:

        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    return incidents[incident_id]


# ==================================================
# ACKNOWLEDGE INCIDENT
# ==================================================

@app.post(
    "/incident/{incident_id}/acknowledge",
    response_model=AcknowledgementResponse
)
def acknowledge_incident(
    incident_id: str
):

    if incident_id not in incidents:

        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    incident = incidents[incident_id]

    # Already acknowledged
    if incident["status"] == "ACKNOWLEDGED":

        return {
            "incident_id": incident_id,
            "status": "ACKNOWLEDGED",
            "acknowledged_at": incident["acknowledged_at"]
        }

    # Already escalated
    if incident["status"] == "ESCALATED":

        raise HTTPException(
            status_code=409,
            detail=(
                "Incident has already been escalated "
                "because no acknowledgement was received."
            )
        )

    # Record acknowledgement
    acknowledged_at = current_time()

    incident["status"] = "ACKNOWLEDGED"

    incident["acknowledged_at"] = acknowledged_at

    print(
        f"[ACKNOWLEDGED] {incident_id}"
    )

    return {
        "incident_id": incident_id,
        "status": "ACKNOWLEDGED",
        "acknowledged_at": acknowledged_at
    }