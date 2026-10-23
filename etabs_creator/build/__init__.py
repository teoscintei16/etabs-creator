"""Constructia unui model in ETABS: geometrie (nivel cu nivel), plansee, rezemare, apoi regulile; pasii sunt in fisiere separate."""
from __future__ import annotations

from pathlib import Path

from ..connect import assert_safe_to_overwrite
from ..plan import build_plan
from ..spec import ModelSpec
from .basement import basement_walls, soil_loads
from .context import Ctx
from .finish import apply_rules, save_and_summarize
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


def build_model(sap, spec: ModelSpec, out_path: str | Path | None = None) -> dict:
    """Creeaza modelul in `sap` (cSapModel) si il salveaza la `out_path`. Intoarce un sumar (obiecte create, note, parametrii proiectului)."""
    spec = spec.validate()
    if spec.tall:
        from .tall import build_tall
        return build_tall(sap, spec, out_path)
    if spec.opera:
        from .opera import build_opera
        return build_opera(sap, spec, out_path)
    if spec.free_shape:
        from .free_model import build_free_model
        return build_free_model(sap, spec, out_path)
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
    notes = apply_rules(c, extra_perm)
    return save_and_summarize(c, notes, base_nodes, out_path,
                              {"piers": sorted({r["pier"] for r in plan.runs}), "stories": [s.name for s in reversed(plan.stories)], "towers": len(plan.towers)})
