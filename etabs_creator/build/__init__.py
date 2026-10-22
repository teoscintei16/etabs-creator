"""Constructia unui model in ETABS: geometrie (nivel cu nivel), plansee, rezemare, apoi regulile; pasii sunt in fisiere separate."""
from __future__ import annotations

from pathlib import Path

from ..connect import assert_safe_to_overwrite, ok
from ..plan import build_plan
from ..rules import (apply_beam_insertion, apply_combinations, apply_cracking, apply_mass_source, apply_mesh, apply_modal,
                     apply_rigid_zones, apply_seismic, calibrate_static)
from ..spec import ModelSpec
from .basement import basement_walls, soil_loads
from .context import Ctx
from .members import columns_and_beams
from .project import default_path, project_params
from .restraints import restrain_base
from .sections import define_sections
from .slabs import define_diaphragm_and_patterns, slabs
from .stories import new_grid
from .walls import coupling_beams, define_piers, wall_panels

__all__ = ["build_model", "default_path", "project_params"]


def _geometry(c: Ctx) -> None:
    define_piers(c)
    for idx in range(len(c.plan.stories)):
        columns_and_beams(c, idx)
        if "wall" in c.sec:
            wall_panels(c, idx)
        if "cbeam" in c.sec:
            coupling_beams(c, idx)
        if "bwall" in c.sec:
            basement_walls(c, idx)
    define_diaphragm_and_patterns(c)
    slabs(c)


def _rules(c: Ctx, extra_perm: list[str]) -> list[str]:
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


def build_model(sap, spec: ModelSpec, out_path: str | Path | None = None) -> dict:
    """Creeaza modelul in `sap` (cSapModel) si il salveaza la `out_path`. Intoarce un sumar (obiecte create, note, parametrii proiectului)."""
    spec = spec.validate()
    assert_safe_to_overwrite(sap)
    plan = build_plan(spec)
    new_grid(sap, spec, plan)
    sec = define_sections(sap, spec)
    c = Ctx(sap, spec, plan, sec, [i * spec.span_x for i in range(spec.bays + 1)], [j * spec.span_y for j in range(spec.travei + 1)])
    if "bwall" in sec:
        c.count["pereti_subsol"] = 0
    _geometry(c)
    extra_perm = soil_loads(c)
    base_nodes = restrain_base(c)
    notes = _rules(c, extra_perm)
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
    return {"spec": spec.to_flat(), "sections": sec, "objects": c.count, "base_nodes": base_nodes, "file": str(path) if path else None,
            "notes": notes, "project": project_params(spec) if spec.seismic else {},
            "belts": {"has": True, "sections": [sec["belt"]]} if "belt" in sec else None,
            "piers": sorted({r["pier"] for r in plan.runs}), "stories": [s.name for s in reversed(plan.stories)],
            "towers": len(plan.towers)}
