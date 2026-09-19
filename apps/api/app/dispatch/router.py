from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.supabase_client import supabase

router = APIRouter(prefix="/dispatch", tags=["dispatch"])


@router.get("/health")
def dispatch_health() -> dict:
    return {"ok": True, "module": "dispatch"}


class AcceptRequest(BaseModel):
    incident_id: str
    offer_id: str
    agency_id: str
    ambulance_id: str | None = None


class AcceptResponse(BaseModel):
    success: bool
    reason: str | None = None
    assigned_agency: str | None = None
    accepted_at: str | None = None


@router.post("/accept", response_model=AcceptResponse)
def accept(req: AcceptRequest) -> AcceptResponse:
    """
    Atomic accept via the accept_dispatch() Postgres function.
    The SQL function is the only correct arbiter of the race;
    this handler just relays the result.
    """
    try:
        rpc = supabase.rpc("accept_dispatch", {
            "p_incident_id": req.incident_id,
            "p_offer_id": req.offer_id,
            "p_agency_id": req.agency_id,
            "p_ambulance_id": req.ambulance_id,
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"rpc_failed: {e}")

    row = (rpc.data or [{}])[0]
    if not row.get("success"):
        reason = row.get("reason", "unknown")
        # 410 if the offer expired, 409 for any other race/state conflict
        code = 410 if reason == "offer_expired" else 409
        raise HTTPException(status_code=code, detail=reason)

    return AcceptResponse(
        success=True,
        assigned_agency=row.get("assigned_agency"),
        accepted_at=str(row.get("accepted_at")) if row.get("accepted_at") else None,
    )