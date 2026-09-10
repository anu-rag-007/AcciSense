from pydantic import BaseModel
from typing import Optional


class IncidentRequest(BaseModel):
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


class IncidentResponse(BaseModel):
    incident_id: str
    incident_type: str
    location: str
    severity: str
    priority: str
    status: str

    severity_score: Optional[float] = None
    people_affected: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    event_time: Optional[str] = None
    ai_confidence: Optional[float] = None

    acknowledged_at: Optional[str] = None
    escalated_at: Optional[str] = None


class AcknowledgementResponse(BaseModel):
    incident_id: str
    status: str
    acknowledged_at: Optional[str] = None