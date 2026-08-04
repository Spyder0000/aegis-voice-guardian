"""
AEGIS Voice Guardian — FastAPI entrypoint.
Owner: Agoro Oluwatimilehin
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import voice, transfers

app = FastAPI(title="AEGIS Voice Guardian")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice.router, prefix="/voice", tags=["voice"])
app.include_router(transfers.router, prefix="/transfers", tags=["transfers"])


@app.get("/health")
def health():
    return {"status": "ok"}
