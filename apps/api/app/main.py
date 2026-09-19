from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.dispatch.router import router as dispatch_router
from app.incidents.router import router as incidents_router
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

app = FastAPI(title="AcciSense app API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dispatch_router, prefix="/api")
app.include_router(incidents_router, prefix="/api")

@app.get("/health")
def health():
    return {"ok": True, "env": settings.env}