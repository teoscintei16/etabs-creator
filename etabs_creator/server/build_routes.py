"""Endpoint-uri de constructie a modelelor."""
from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..build import build_model, default_path
from ..connect import OUT_DIR, GenError
from ..defects import DESCRIPTIONS
from ..sidecar import write_settings
from ..spec import PARTS, STRUCTURES, ModelSpec
from ..spec.sections import CONCRETE
from .recovery import build_with_recovery
from .state import STATE, alive, run

router = APIRouter()


class BuildRequest(BaseModel):
    spec: dict


@router.get("/api/defaults")
def defaults():
    return {"spec": ModelSpec().to_flat(), "concrete": list(CONCRETE), "structures": list(STRUCTURES), "parts": list(PARTS),
            "out_dir": str(OUT_DIR), "defects": DESCRIPTIONS, "models": STATE["models"]}


@router.post("/api/build")
def build(req: BuildRequest):
    try:
        spec = ModelSpec.from_flat(req.spec)
    except GenError as e:
        raise HTTPException(422, str(e)) from e

    def _f():
        if not alive():
            raise GenError("ETABS nu este pornit: apasă „Deschide ETABS”.")
        t0 = time.time()
        res = build_with_recovery(lambda: build_model(STATE["obj"].SapModel, spec, default_path(spec, OUT_DIR)))
        res["seconds"] = round(time.time() - t0, 1)
        res["sidecar"] = write_settings(res["file"], res["project"], res.get("belts"), res.get("params")) if res["file"] and res["project"] else None
        STATE["models"].append({"file": res["file"], "objects": res["objects"], "name": spec.name, "structure": spec.structure})
        return res
    return run(_f)
