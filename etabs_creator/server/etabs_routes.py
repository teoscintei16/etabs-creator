"""Endpoint-uri pentru instanta ETABS: stare, pornire (sau atasare la una goala/generata), inchidere."""
from __future__ import annotations

import time

from fastapi import APIRouter

from ..connect import attach_if_safe, start_etabs
from .state import STATE, alive, run

router = APIRouter()


@router.get("/api/status")
def status():
    def _f():
        if not alive():
            return {"open": False}
        sap = STATE["obj"].SapModel
        return {"open": True, "file": sap.GetModelFilename() or "", "version": str(sap.GetVersion()[0])}
    return run(_f)


@router.post("/api/open")
def open_etabs():
    """Porneste o instanta ETABS noua; se ataseaza la una existenta doar daca nu are modelul unui utilizator."""
    def _f():
        if alive():
            return {"open": True, "already": True}
        t0 = time.time()
        STATE["obj"] = attach_if_safe()
        if STATE["obj"] is not None:
            return {"open": True, "already": True}
        STATE["obj"] = start_etabs()
        return {"open": True, "already": False, "seconds": round(time.time() - t0, 1)}
    return run(_f)


@router.post("/api/close")
def close_etabs():
    def _f():
        if alive():
            STATE["obj"].ApplicationExit(False)
            STATE["obj"] = None
        return {"open": False}
    return run(_f)
