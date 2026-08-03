"""
AEGIS Voice Guardian — FastAPI entrypoint.
Owner: Agoro Oluwatimilehin
"""
from fastapi import FastAPI
from app.routers import voice, transfers

app = FastAPI(title="AEGIS Voice Guardian")

app.include_router(voice.router, prefix="/voice", tags=["voice"])
app.include_router(transfers.router, prefix="/transfers", tags=["transfers"])


@app.get("/health")
def health():
    return {"status": "ok"}
