from pydantic import BaseModel
from typing import Optional


class IncidentRequest(BaseModel):
    incident_type: str
    location: str
    severity_indicator: str


class IncidentResponse(BaseModel):
    incident_id: str
    incident_type: str
    location: str
    severity: str
    priority: str
    status: str
    acknowledged_at: Optional[str] = None
    escalated_at: Optional[str] = None


class AcknowledgementResponse(BaseModel):
    incident_id: str
    status: str
    acknowledged_at: Optional[str] = None