"""Defecte la elemente: fara zone rigide, plăci fara diafragma, noduri cu zecimale parazite, grinzi secundare fara eliberari, etichete Pier repetate."""
from __future__ import annotations

from ..connect import ok
from ..tables import read_table, update_rows
from .registry import defect


@defect("no_rigid_zones", "factor de zona rigida 0 pe toate barele")
def no_rigid_zones(c) -> str:
    n = update_rows(c.sap, "Frame Assignments - End Length Offsets", {f: {"RigidFact": "0"} for f in c.frames}, "UniqueName")
    return f"zone rigide: factor 0 la {n} bare"


@defect("slab_no_diaphragm", "trei plăci fara diafragma")
def slab_no_diaphragm(c) -> str:
    victims = c.slabs[-3:]
    for name in victims:
        ok(c.sap.AreaObj.SetDiaphragm(name, "None"), "AreaObj.SetDiaphragm")
    return f"{len(victims)} plăci fără diafragmă"


@defect("parasitic_nodes", "trei noduri cu zecimale parazite (unul aproape de 0)")
def parasitic_nodes(c) -> str:
    _v, _f, rows = read_table(c.sap, "Point Object Connectivity")
    free = [r for r in rows if r["IsAuto"] == "No" and float(r["Z"]) > 0]
    zero = next((r for r in free if abs(float(r["X"])) < 1e-9), None)
    other = [r for r in free if r is not zero and abs(float(r["X"])) > 1e-9][:2]
    changes = {r["UniqueName"]: {"X": f"{float(r['X']) + 0.00003:.6f}"} for r in other}
    if zero:
        changes[zero["UniqueName"]] = {"X": "0.00002"}
    update_rows(c.sap, "Point Object Connectivity", changes, "UniqueName")
    return f"{len(changes)} noduri cu coordonate parazite"


@defect("secondary_beams", "grinda secundara care reazema pe interiorul altor grinzi, fara eliberari")
def secondary_beams(c) -> str:
    st = next(s for s in c.plan.stories if not s.basement)
    xm = (c.xs[0] + c.xs[1]) / 2
    name = c.add_frame((xm, c.ys[0], st.z_top), (xm, c.ys[1], st.z_top), c.sec["beam"], "grindă secundară")
    return f"grinda secundară {name} la x = {xm:g} m, fără eliberări"


@defect("pier_same_labels", "aceleasi etichete Pier la turnuri diferite")
def pier_same_labels(c) -> str:
    plain = {}
    for name, pier in c.pier_areas:
        plain[pier] = pier.split("_", 1)[-1] if pier[:1] == "T" and "_" in pier else pier
    for p in dict.fromkeys(plain.values()):
        c.sap.PierLabel.SetPier(p)
    for name, pier in c.pier_areas:
        ok(c.sap.AreaObj.SetPier(name, plain[pier]), "AreaObj.SetPier")
    return "etichete Pier fără prefix de turn: " + ", ".join(sorted(set(plain.values())))
