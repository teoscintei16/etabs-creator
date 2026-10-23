"""Constructia operei: podium ortogonal (motorul existent) + cutiile salilor + coji sferice cu coaste, pe niveluri suplimentare pentru forte seismice."""
from __future__ import annotations

import math
from pathlib import Path
from types import SimpleNamespace

from ..connect import assert_safe_to_overwrite
from ..plan import build_plan
from ..plan.stories import Story
from ..shells.layout import build_layout
from .basement import basement_walls, soil_loads
from .context import Ctx
from .finish import apply_rules, save_and_summarize
from .members import columns_and_beams
from .opera_podium import hall_walls, podium_overrides
from .opera_sections import opera_sections
from .opera_shells import build_shell, define_loads, ridge_ties
from .restraints import restrain_base
from .sections import define_sections
from .slabs import define_diaphragm_and_patterns, slabs
from .stories import new_grid
from .walls import define_piers, wall_panels


def prepare(spec):
    """Podiumul cere pereti (doar cei ai salilor, desenati aici), goluri in sali si fara grinzi de cuplare."""
    layout = build_layout(spec)
    spec.void_cells = layout.void_text()
    spec.walls, spec.wall_lines_y, spec.wall_bays_y = True, "none", "none"            # pereti pe Y: doar peretii salilor (desenati in opera_podium)
    spec.wall_lines_x, spec.wall_bays_x = spec.podium_wall_lines, spec.podium_wall_bays
    spec.coupling_bays_x = spec.coupling_bays_y = spec.core_shape = ""
    return layout


def shell_stories(spec, layout, plan) -> list[Story]:
    """Nivelurile de deasupra podiumului, pana la creasta cea mai inalta."""
    top = max(sh.mesh(spec).max_z() for sh in layout.shells)
    h = math.ceil(top - layout.z0) / spec.shell_stories
    z = plan.stories[-1].z_top
    return [Story(f"T{k}", z + (k - 1) * h, z + k * h, False) for k in range(1, spec.shell_stories + 1)]


def build_opera(sap, spec, out_path: str | Path | None = None) -> dict:
    assert_safe_to_overwrite(sap)
    layout = prepare(spec)
    plan = build_plan(spec)
    extra = shell_stories(spec, layout, plan)
    new_grid(sap, spec, SimpleNamespace(stories=plan.stories + extra))
    sec = define_sections(sap, spec)
    sec.update(opera_sections(sap, spec, sec["material"]))
    c = Ctx(sap, spec, plan, sec, [i * spec.span_x for i in range(spec.bays + 1)], [j * spec.span_y for j in range(spec.travei + 1)])
    c.count["pereti_subsol"] = 0
    c.count["pereti"] = 0
    podium_overrides(c, layout)
    define_piers(c)
    for idx in range(len(plan.stories)):
        columns_and_beams(c, idx)
        wall_panels(c, idx)
        basement_walls(c, idx)
    hall_walls(c, layout)
    define_diaphragm_and_patterns(c)
    slabs(c)
    define_loads(c)
    meshes = {sh.name: build_shell(c, sh) for sh in layout.shells}
    ridge_ties(c, meshes, layout)
    extra_perm = soil_loads(c)
    base_nodes = restrain_base(c)
    crest = extra[-1].z_top
    notes = [f"operă: {len(layout.shells)} coji sferice (R = {spec.opera_radius:g} m), {len(layout.halls)} săli, "
             f"{len(extra)} niveluri de coji până la {crest:g} m"] + apply_rules(c, extra_perm)
    return save_and_summarize(c, notes, base_nodes, out_path,
                              {"piers": sorted({f"{h.name}_{t}" for h in layout.halls for t in "WESN"} | {r["pier"] for r in plan.runs}),
                               "stories": [s.name for s in reversed(plan.stories + extra)], "towers": 1})
