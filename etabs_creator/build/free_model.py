"""Constructia unei structuri cu plan liber (cerc, semicerc, spline, trapez, piramide…)."""
from __future__ import annotations

from pathlib import Path

from ..connect import assert_safe_to_overwrite
from ..free import FreePlan, build_free_plan
from .context import Ctx
from .finish import apply_rules, save_and_summarize
from .free_members import columns_and_beams
from .free_walls import basement_walls, soil_loads, wall_panels
from .restraints import restrain_base
from .sections import define_sections
from .slabs import add_slab, define_diaphragm_and_patterns
from .stories import new_grid
from .walls import define_piers


def _slabs(c: Ctx, fp: FreePlan) -> None:
    for idx, st in enumerate(fp.stories):
        _lo, hi = fp.levels(idx)
        for face in fp.slab_faces(idx):
            add_slab(c, [(*fp.xy(n, hi), st.z_top) for n in face])


class _PierPlan:
    """Aspectul minim al planului cerut de define_piers: lista peretilor cu eticheta Pier."""

    def __init__(self, fp: FreePlan):
        self.runs = [{"pier": p} for p in dict.fromkeys(fp.piers[j] for j in sorted(fp.piers))]


def build_free_model(sap, spec, out_path: str | Path | None = None) -> dict:
    assert_safe_to_overwrite(sap)
    fp = build_free_plan(spec)
    new_grid(sap, spec, fp)
    sec = define_sections(sap, spec)
    c = Ctx(sap, spec, _PierPlan(fp), sec, [], [])
    if "bwall" in sec:
        c.count["pereti_subsol"] = 0
    if "wall" in sec:
        c.count["pereti"] = 0
    define_piers(c)
    for idx in range(len(fp.stories)):
        columns_and_beams(c, fp, idx)
        if "wall" in sec:
            wall_panels(c, fp, idx)
        if "bwall" in sec:
            basement_walls(c, fp, idx)
    define_diaphragm_and_patterns(c)
    _slabs(c, fp)
    extra_perm = soil_loads(c)
    base_nodes = restrain_base(c)
    notes = [f"plan liber „{spec.free_shape}”: {fp.radial.m} puncte pe contur, {spec.free_rings} inele, "
             f"{len(fp.radial.faces())} plăci/nivel" + (f", reducere {spec.taper:g}" if spec.taper else "")
             + (f", trepte la {spec.step_every} etaje ×{spec.step_scale:g}" if spec.step_every else "")] + apply_rules(c, extra_perm)
    return save_and_summarize(c, notes, base_nodes, out_path,
                              {"piers": sorted(set(fp.piers.values())), "stories": [s.name for s in reversed(fp.stories)], "towers": 1})
