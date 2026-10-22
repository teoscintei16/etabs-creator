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


def slabs(c: Ctx) -> None:
    xs, ys, spec = c.xs, c.ys, c.spec
    for idx, st in enumerate(c.plan.stories):
        for i, j in c.plan.slab_cells(idx):
            name = ok(c.sap.AreaObj.AddByCoord(4, [xs[i], xs[i + 1], xs[i + 1], xs[i]], [ys[j], ys[j], ys[j + 1], ys[j + 1]], [st.z_top] * 4, "",
                                               c.sec["slab"]), "AddByCoord (placă)")[-1]
            ok(c.sap.AreaObj.SetDiaphragm(name, "D1"), "AreaObj.SetDiaphragm")
            if spec.dead_extra:
                ok(c.sap.AreaObj.SetLoadUniform(name, "Permanenta", spec.dead_extra, SLAB_DIR_GRAVITY), "SetLoadUniform (perm.)")
            if spec.live:
                ok(c.sap.AreaObj.SetLoadUniform(name, "Live", spec.live, SLAB_DIR_GRAVITY), "SetLoadUniform (utilă)")
            c.bump("placi")
