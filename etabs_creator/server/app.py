"""Aplicatia FastAPI: pagina simpla + endpoint-urile."""
from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .build_routes import router as build_router
from .etabs_routes import router as etabs_router

STATIC = Path(__file__).parent / "static"

app = FastAPI(title="ETABS Creator")
app.include_router(etabs_router)
app.include_router(build_router)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-store"})


def serve(port: int = 8766) -> None:
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
