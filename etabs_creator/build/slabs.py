"""Planseele: diafragma, incarcari uniforme (permanent suplimentar si utila)."""
from __future__ import annotations

from ..connect import GenError, ok
from .context import SLAB_DIR_GRAVITY, SUPER_DEAD, Ctx


def define_diaphragm_and_patterns(c: Ctx) -> None:
    c.sap.Diaphragm.Delete("D1")              # NewGridOnly defineste deja o diafragma D1 (rigida): o redefinim cu tipul cerut
    ok(c.sap.Diaphragm.SetDiaphragm("D1", c.spec.diaphragm == "semirigid"), "SetDiaphragm")
    try:
        ok(c.sap.LoadPatterns.Add("Permanenta", SUPER_DEAD, 0, True), "LoadPatterns.Add")
    except GenError:
        pass                                  # exista deja


def add_slab(c: Ctx, pts: list[tuple[float, float, float]]) -> str:
    """Placa pe un poligon (orice nr. de colturi): diafragma D1 si incarcarile uniforme (permanent suplimentar, utila)."""
    name = c.add_poly(pts, c.sec["slab"], "placă")
    ok(c.sap.AreaObj.SetDiaphragm(name, "D1"), "AreaObj.SetDiaphragm")
    if c.spec.dead_extra:
        ok(c.sap.AreaObj.SetLoadUniform(name, "Permanenta", c.spec.dead_extra, SLAB_DIR_GRAVITY), "SetLoadUniform (perm.)")
    if c.spec.live:
        ok(c.sap.AreaObj.SetLoadUniform(name, "Live", c.spec.live, SLAB_DIR_GRAVITY), "SetLoadUniform (utilă)")
    c.bump("placi")
    c.slabs.append(name)
    return name


def slabs(c: Ctx) -> None:
    xs, ys = c.xs, c.ys
    for idx, st in enumerate(c.plan.stories):
        for i, j in c.plan.slab_cells(idx):
            add_slab(c, [(xs[i], ys[j], st.z_top), (xs[i + 1], ys[j], st.z_top), (xs[i + 1], ys[j + 1], st.z_top), (xs[i], ys[j + 1], st.z_top)])
