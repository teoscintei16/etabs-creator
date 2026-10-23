"""Constructia turnului in Y (Burj Khalifa): niveluri cu inaltimi variabile, sectiuni pe zone, retrageri in spirala, seturi de incarcari pe ocupare,
vant pe inaltime, subsol cu pereti pe contur, spire din otel. Vezi docs/BURJ_CONCEPT.md."""
from __future__ import annotations

import math
from pathlib import Path
from types import SimpleNamespace

from ..connect import assert_safe_to_overwrite
from ..tall.geometry import TowerGeom
from ..tall.levels import build_levels
from ..tall.occupancy import check_sets, parse_occupancy, set_of
from ..tall.setbacks import bays_at
from ..tall.storyplan import story_plan
from ..tall.zones import parse_zones, zone_of
from . import tall_elements as el
from .context import Ctx
from .finish import apply_rules, save_and_summarize
from .free_walls import soil_loads
from .restraints import restrain_base
from .slabs import define_diaphragm_and_patterns
from .staged import define_staged, stage_group
from .stories import new_grid
from .tall_loads import define_temperature, define_wind, load_sets, story_wind
from .tall_sections import SPIRE_OD_BASE, SPIRE_OD_TOP, define_tall_sections


def geometry(spec) -> TowerGeom:
    return TowerGeom(spec.core_radius, spec.wing_halfwidth, spec.corridor_half, spec.wing_bay)


def build_tall(sap, spec, out_path: str | Path | None = None) -> dict:
    assert_safe_to_overwrite(sap)
    g, levels, zones = geometry(spec), build_levels(spec), parse_zones(spec)
    sets, occupancy = check_sets(spec, levels), parse_occupancy(spec.occupancy)
    new_grid(sap, spec, SimpleNamespace(stories=levels))
    ts = define_tall_sections(sap, spec, zones)
    c = Ctx(sap, spec, SimpleNamespace(stories=levels), {"material": zones[0].grade, "belt": ts.belt}, [], [])
    c.sec_all = ts.all
    c.count.update({"pereti": 0, "pereti_subsol": 0})
    el.define_piers(c)
    define_diaphragm_and_patterns(c)
    define_wind(c)
    define_temperature(c)
    assign: dict[str, str] = {}
    full = bays_at(spec, 1)
    hex0 = g.hex_vertex(0)
    first_above = next(i for i, lv in enumerate(levels) if not lv.basement)
    for idx, lv in enumerate(levels):
        if spec.tall_stage_every:
            c.group = stage_group(max(lv.number - 1, 0) // spec.tall_stage_every + 1)
        if lv.kind == "spire":
            el.spire(c, ts, lv, lv.number - spec.tall_levels - 1, [g.hex_vertex(i) for i in range(6)])
            od = SPIRE_OD_BASE + (SPIRE_OD_TOP - SPIRE_OD_BASE) * ((lv.number - spec.tall_levels - 1) / max(spec.tall_spire_levels - 1, 1))
            story_wind(c, lv, (0.0, 0.0), (od, od))
            continue
        base = lv.basement
        sp = story_plan(g, full if base else bays_at(spec, lv.number))
        z = zones[0] if base else zone_of(zones, lv.number)
        secs = ts.of(z)
        el.walls(c, ts, lv, sp, secs["wall"], first=idx == 0)
        if base:
            el.basement_outline(c, ts, lv, sp, first=idx == 0)
        else:
            el.columns(c, lv, sp, secs["column"])
        el.beams(c, lv, sp, secs, spec.facade_load, base)
        el.slabs(c, lv, sp, secs["slab"], set_of(lv, occupancy), assign)
        if not base:
            story_wind(c, lv, hex0, sp.extents())
    notes = [f"turn în Y: {spec.tall_levels} niveluri de beton + {spec.tall_spire_levels} de spire, {len(zones)} zone de secțiuni, "
             f"{len(levels)} niveluri, vârf la {levels[-1].z_top:g} m", load_sets(c, sets, assign)]
    if spec.tall_stage_every:
        c.group = ""
        notes.append(define_staged(c))
    extra_perm = soil_loads(c)
    base_nodes = restrain_base(c)
    notes += apply_rules(c, extra_perm)
    stories_above = len([lv for lv in levels if not lv.basement])
    params = {"r5_mesh.mesh_max": spec.mesh_max}
    if spec.modes_total:
        params["r10_moduri.moduri_per_etaj"] = math.floor(spec.modes_total / stories_above * 100) / 100
    return save_and_summarize(c, notes, base_nodes, out_path,
                              {"piers": sorted(el.PIERS), "stories": [lv.name for lv in reversed(levels)], "towers": 1, "params": params})
