"""Partea comuna a oricarui model, dupa geometrie: regulile (fisurare, zone rigide, mesh, masa, moduri, seism, combinatii), salvarea si calibrarea."""
from __future__ import annotations

from pathlib import Path

from ..connect import ok
from ..rules import (apply_beam_insertion, apply_combinations, apply_cracking, apply_mass_source, apply_mesh, apply_modal, apply_rigid_zones,
                     apply_seismic, calibrate_static)
from .context import Ctx
from .project import project_params


def apply_rules(c: Ctx, extra_perm: list[str]) -> list[str]:
    """Aplica regulile; intoarce notele pentru raport."""
    sap, spec = c.sap, c.spec
    has_perm = bool(spec.dead_extra)
    notes = [apply_cracking(sap, spec, c.sec), apply_rigid_zones(sap, c.frames, spec.rigid_zone), apply_beam_insertion(sap, c.beams),
             apply_mesh(sap, spec.mesh_max), apply_mass_source(sap, spec, has_perm), apply_modal(sap, spec)]
    static, cases = [], []
    if spec.seismic:
        top = ok(sap.Story.GetNameList(), "Story.GetNameList")[1][0]            # primul = nivelul cel mai de sus
        static, cases, extra = apply_seismic(sap, spec, top, "S1" if spec.basement else "Base")   # cu subsol, fortele seismice incep de la S1 (±0.00)
        notes += extra
    notes.append(f"{apply_combinations(sap, spec, has_perm, static, cases, extra_perm)} combinații (ULS, SLS, seismice)")
    if spec.basement and spec.soil_pressure:
        notes.append(f"subsol {spec.basement} niveluri: pereți perimetrali {spec.basement_wall_t * 100:g} cm, "
                     f"împingerea pământului {spec.soil_pressure:g} kN/m² (uniformă)")
    return notes


def save_and_summarize(c: Ctx, notes: list[str], base_nodes: int, out_path: str | Path | None, extra: dict) -> dict:
    """Salveaza modelul (si calibreaza fortele statice dupa T1) si intoarce sumarul. `extra` = piers, stories, towers…"""
    sap, spec = c.sap, c.spec
    if hasattr(sap, "View"):
        sap.View.RefreshView(0, False)
    path = None
    if out_path:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        ok(sap.File.Save(str(path)), "File.Save")
        if spec.seismic and spec.calibrate_static:
            notes.append(calibrate_static(sap, spec))
            ok(sap.File.Save(str(path)), "File.Save (după calibrare)")
    return {"spec": spec.to_flat(), "sections": c.sec, "objects": c.count, "base_nodes": base_nodes, "file": str(path) if path else None,
            "notes": notes, "project": project_params(spec) if spec.seismic else {},
            "belts": {"has": True, "sections": [c.sec["belt"]]} if "belt" in c.sec else None, **extra}
