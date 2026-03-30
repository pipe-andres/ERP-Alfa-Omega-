from fastapi import FastAPI
from src.api.routes import router as api_router

app = FastAPI(title="Inventario API - FASE 2 (Scaffold)")

app.include_router(api_router, prefix="/api")


@app.get("/", tags=["root"])
async def root():
    return {"ok": True, "service": "Inventario API", "version": "fase-2-scaffold"}
