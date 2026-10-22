"""Peretii perimetrali de subsol (cu centura dummy deasupra) si impingerea pamantului."""
from __future__ import annotations

from ..connect import ok
from .context import LOCAL_3, OTHER, SOIL_PATTERN, Ctx


def basement_walls(c: Ctx, idx: int) -> None:
    st = c.plan.stories[idx]
    for w in c.plan.basement_walls(idx):
        name, px, py = c.add_panel(w["axis"], w["line"], w["bay"], st.z_bot, st.z_top, c.sec["bwall"], "perete subsol")
        c.bump("pereti_subsol")
        c.soil_areas.append((name, w["axis"], w["side"]))
        if idx == 0:
            c.restrain_panel_base(name)
        if "belt" in c.sec:                       # grinzile care se descarca in nodul peretelui au nevoie de centura
            c.beams.append(c.add_frame((px[0], py[0], st.z_top), (px[1], py[1], st.z_top), c.sec["belt"], "centură subsol"))
            c.bump("centuri")


# presiunea actioneaza spre interior; axa locala 3 a panoului: pe X -> -y, pe Y -> +x
INWARD = {("X", "lo"): -1.0, ("X", "hi"): 1.0, ("Y", "lo"): 1.0, ("Y", "hi"): -1.0}


def soil_loads(c: Ctx) -> list[str]:
    """Creeaza tiparul de impingere si il asigneaza pe peretii de subsol. Intoarce tiparele permanente suplimentare pentru combinatii."""
    if not (c.spec.basement and c.spec.soil_pressure):
        return []
    ok(c.sap.LoadPatterns.Add(SOIL_PATTERN, OTHER, 0, True), "LoadPatterns.Add (pământ)")
    for name, axis, side in c.soil_areas:
        ok(c.sap.AreaObj.SetLoadUniform(name, SOIL_PATTERN, INWARD[(axis, side)] * c.spec.soil_pressure, LOCAL_3, True, "Local"),
           "SetLoadUniform (pământ)")
    return [SOIL_PATTERN]
