# backend/admin_auth.py  (new file — main.py untouched except 2 lines below)
import os, bcrypt, jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client

router = APIRouter(tags=["admin"])
_sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
SECRET = os.getenv("JWT_SECRET", "accisense-demo-secret")

class LoginReq(BaseModel):
    admin_id: str
    password: str

@router.post("/admin/login")
async def admin_login(req: LoginReq):
    row = _sb.table("admins").select("*").eq("admin_id", req.admin_id).execute()
    if not row.data or not bcrypt.checkpw(req.password.encode(), row.data[0]["password_hash"].encode()):
        raise HTTPException(401, "Invalid admin credentials")
    a = row.data[0]
    token = jwt.encode({"sub": a["admin_id"], "role": a["role"], "zone": a.get("zone"),
                        "exp": datetime.utcnow() + timedelta(hours=8)}, SECRET, algorithm="HS256")
    return {"access_token": token, "role": a["role"], "zone": a.get("zone"), "name": a["name"]}