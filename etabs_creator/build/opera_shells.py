"""Cojile operei: arii pe reteaua sferica, coaste, grinda de picior, grinda frontala, legaturi de coama intre coaja si contra-coaja, incarcari."""
from __future__ import annotations

from ..connect import ok
from ..shells import ShellMesh
from ..shells.layout import Layout, ShellDef
from .context import SLAB_DIR_GRAVITY, Ctx

WIND_TYPE, TEMPERATURE_TYPE, TEMP_LOAD = 6, 10, 1          # tipul tiparului Wind / Temperature; tipul incarcarii de temperatura (1 = temperatura)
PROJECTED_X, PROJECTED_Y = 7, 8
TIE_MAX_GAP = 20.0                  # m: legatura de coama doar unde coaja si contra-coaja sunt mai aproape de atat


def define_loads(c: Ctx) -> None:
    """Tiparele de vant (presiune pe proiectia cojilor) si de temperatura; Permanenta exista deja (define_diaphragm_and_patterns)."""
    if c.spec.wind > 0:
        for name in ("Vant_X", "Vant_Y"):
            ok(c.sap.LoadPatterns.Add(name, WIND_TYPE, 0, True), f"LoadPatterns.Add ({name})")
            c.variable.append(name)
    if c.spec.shell_temp > 0:
        ok(c.sap.LoadPatterns.Add("Temp", TEMPERATURE_TYPE, 0, True), "LoadPatterns.Add (Temp)")
        c.variable.append("Temp")


def _frames(c: Ctx, pts, prop: str, what: str, key: str) -> None:
    for p, q in zip(pts, pts[1:]):
        c.add_frame(p, q, c.sec[prop], what)
        c.bump(key)


def _shell_area(c: Ctx, face) -> None:
    spec = c.spec
    name = c.add_poly(list(face), c.sec["shell"], "coajă")
    if spec.shell_cladding:
        ok(c.sap.AreaObj.SetLoadUniform(name, "Permanenta", spec.shell_cladding, SLAB_DIR_GRAVITY), "SetLoadUniform (placări)")
    if spec.shell_live:
        ok(c.sap.AreaObj.SetLoadUniform(name, "Live", spec.shell_live, SLAB_DIR_GRAVITY), "SetLoadUniform (utilă)")
    for pat, d in (("Vant_X", PROJECTED_X), ("Vant_Y", PROJECTED_Y)):
        if pat in c.variable:
            ok(c.sap.AreaObj.SetLoadUniform(name, pat, spec.wind, d, True, "Global"), f"SetLoadUniform ({pat})")
    if "Temp" in c.variable:
        ok(c.sap.AreaObj.SetLoadTemperature(name, "Temp", TEMP_LOAD, spec.shell_temp), "SetLoadTemperature")
    c.bump("coji")


def build_shell(c: Ctx, sh: ShellDef) -> ShellMesh:
    """Coaja `sh` cu toate elementele ei; intoarce reteaua (pentru legaturile de coama)."""
    mesh = sh.mesh(c.spec)
    for face in mesh.faces():
        _shell_area(c, face)
    _frames(c, mesh.base_nodes(), "foot", "grindă de picior", "grinzi_picior")
    _frames(c, mesh.rim(), "rim", "grindă frontală", "grinzi_frontale")
    for j in sorted(set(range(c.spec.shell_rib_every, mesh.m + 1, c.spec.shell_rib_every)) | {mesh.m}):
        _frames(c, mesh.rib(j), "rib", "coastă", "coaste")
    return mesh


def ridge_ties(c: Ctx, meshes: dict[str, ShellMesh], layout: Layout) -> None:
    """Legaturi de coama: intre nodul muchiei frontale al coajii W si al contra-cojii E (oglindite fata de axa) cand golul dintre ele e mic."""
    by_key = {(s.hall, s.row, s.side): s for s in layout.shells}
    for (hall, row, side), sh in by_key.items():
        other = by_key.get((hall, row, "E"))
        if side != "W" or other is None:
            continue
        rw, re = meshes[sh.name].rim(), meshes[other.name].rim()
        for p, q in zip(rw, re):
            if 0.5 < abs(q[0] - p[0]) <= TIE_MAX_GAP:
                c.add_frame(p, q, c.sec["tie"], "legătură de coamă")
                c.bump("legaturi_coama")
