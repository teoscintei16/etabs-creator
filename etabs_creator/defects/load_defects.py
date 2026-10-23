"""Defecte de incarcari: greutate proprie lipsa sau dublata, tipuri de tipare nepotrivite cu numele."""
from __future__ import annotations

from ..connect import ok
from .registry import defect

DEAD = 1


@defect("selfwt_none", "niciun tipar nu include greutatea proprie")
def selfwt_none(c) -> str:
    ok(c.sap.LoadPatterns.SetSelfWTMultiplier("Dead", 0.0), "SetSelfWTMultiplier")
    return "greutatea proprie: multiplicator 0 la Dead"


@defect("selfwt_double", "greutatea proprie inclusa si in Permanenta")
def selfwt_double(c) -> str:
    ok(c.sap.LoadPatterns.SetSelfWTMultiplier("Permanenta", 1.0), "SetSelfWTMultiplier")
    return "greutatea proprie dublată: multiplicator 1 și la Permanenta"


@defect("pattern_type_wrong", "tipare „zapada” si „utila_etaj” definite ca Dead")
def pattern_type_wrong(c) -> str:
    for name in ("zapada", "utila_etaj"):
        ok(c.sap.LoadPatterns.Add(name, DEAD, 0, True), f"LoadPatterns.Add({name})")
    return "tipare „zapada” și „utila_etaj” cu tipul Dead"
