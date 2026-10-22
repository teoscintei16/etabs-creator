"""Planul liber: pereti pe laturile conturului (trapezoidali la piramide), pereti de subsol, impingerea pamantului."""
from __future__ import annotations

from ..connect import ok
from ..free import FreePlan
from .context import LOCAL_3, OTHER, SOIL_PATTERN, Ctx


def _panel(c: Ctx, fp: FreePlan, idx: int, j: int, prop: str, what: str):
    """Panou pe latura j a conturului: jos pe nivelul de jos, sus pe cel de sus (trapez cand scara difera). Ordinea punctelor da axa locala 3 spre exterior."""
    st = fp.stories[idx]
    lo, hi = fp.levels(idx)
    n0, n1 = fp.radial.boundary_edge(j)
    b0, b1 = fp.xy(n0, lo), fp.xy(n1, lo)
    t0, t1 = fp.xy(n0, hi), fp.xy(n1, hi)
    pts = [(*b0, st.z_bot), (*b1, st.z_bot), (*t1, st.z_top), (*t0, st.z_top)]
    return c.add_poly(pts, prop, what), (t0, t1)


def _belt(c: Ctx, st, top_edge) -> None:
    t0, t1 = top_edge
    c.beams.append(c.add_frame((*t0, st.z_top), (*t1, st.z_top), c.sec["belt"], "centură"))
    c.bump("centuri")


def wall_panels(c: Ctx, fp: FreePlan, idx: int) -> None:
    st = fp.stories[idx]
    for w in fp.wall_panels(idx):
        name, top = _panel(c, fp, idx, w["edge"], c.sec["wall"], "perete")
        lo, hi = fp.levels(idx)
        if lo == hi:                                    # ETABS accepta eticheta Pier doar pe panouri verticale (cele inclinate sunt „rampe”)
            ok(c.sap.AreaObj.SetPier(name, w["pier"]), "AreaObj.SetPier")
        else:
            c.bump("pereti_inclinati")
        c.bump("pereti")
        if idx == 0:
            c.restrain_panel_base(name)
        if "belt" in c.sec:
            _belt(c, st, top)


def basement_walls(c: Ctx, fp: FreePlan, idx: int) -> None:
    st = fp.stories[idx]
    for w in fp.basement_walls(idx):
        name, top = _panel(c, fp, idx, w["edge"], c.sec["bwall"], "perete subsol")
        c.bump("pereti_subsol")
        c.soil_areas.append((name, "free", "out"))
        if idx == 0:
            c.restrain_panel_base(name)
        if "belt" in c.sec:
            _belt(c, st, top)


def soil_loads(c: Ctx) -> list[str]:
    """Impingerea pamantului spre interior: axa locala 3 a panourilor e spre exterior, deci valoarea e negativa."""
    if not (c.spec.basement and c.spec.soil_pressure):
        return []
    ok(c.sap.LoadPatterns.Add(SOIL_PATTERN, OTHER, 0, True), "LoadPatterns.Add (pământ)")
    for name, _axis, _side in c.soil_areas:
        ok(c.sap.AreaObj.SetLoadUniform(name, SOIL_PATTERN, -c.spec.soil_pressure, LOCAL_3, True, "Local"), "SetLoadUniform (pământ)")
    return [SOIL_PATTERN]
