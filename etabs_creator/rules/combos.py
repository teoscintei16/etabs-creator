"""Combinatiile de incarcari in model (ULS, SLS, seismice) prin RespCombo."""
from __future__ import annotations

from ..connect import ok
from ..seismic import combos, params_from

LOAD_CASE = 0                                   # eCNameType.LoadCase (tiparele au cazuri liniare cu acelasi nume)


def apply_combinations(sap, spec, has_perm: bool, static: list[str], rs: list[str], extra_perm: list[str] | None = None,
                       wind: list[str] | None = None, extra: list | None = None) -> int:
    items = combos(has_perm, static, rs, params_from(spec), spec.gamma_g, spec.gamma_q, extra_perm or (), wind or ())
    items = list(items) + list(extra or [])
    for name, parts in items:
        ok(sap.RespCombo.Add(name, 0), f"RespCombo.Add({name})")
        for load, sf in parts:
            ok(sap.RespCombo.SetCaseList(name, LOAD_CASE, load, float(sf)), f"RespCombo.SetCaseList({name}, {load})")
    return len(items)
