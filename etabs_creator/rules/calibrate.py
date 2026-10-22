"""Calibrarea fortelor statice: C = λ·Sd(T1)/g pe fiecare directie, dupa o analiza modala (ca un proiectant)."""
from __future__ import annotations

from ..connect import GenError, ok
from ..seismic import coefficient_for_period, params_from
from ..tables import read_display, read_table, update_rows
from .seismic import COEFF_TABLE


def dominant_periods(modes: list[dict]) -> dict[str, float]:
    """T1 pe directie = perioada modului cu masa participanta maxima pe acea directie (ca in verificator)."""
    return {ax: float(max(modes, key=lambda r: float(r[f"U{ax}"]))["Period"]) for ax in ("X", "Y")}


def calibrate_static(sap, spec) -> str:
    """Ruleaza analiza (modelul trebuie salvat), citeste T1 pe X si Y si rescrie C in tiparele EXP/EXN/EYP/EYN.
    Dupa analiza modelul e blocat, iar editarea tabelelor e ignorata in tacere: se deblocheaza si se confirma prin citire."""
    code = sap.Analyze.RunAnalysis()
    if code != 0:
        raise GenError(f"Analiza pentru calibrarea forțelor statice a eșuat (cod {code}).")
    modes = read_display(sap, "Modal Participating Mass Ratios")
    if not modes:
        return "calibrare forțe statice omisă: nu există rezultate modale"
    p = params_from(spec)
    t1 = dominant_periods(modes)
    changes = {f"E{ax}{sg}": {"C": f"{coefficient_for_period(t1[ax], p):g}"} for ax in ("X", "Y") for sg in ("P", "N")}
    if sap.GetModelIsLocked():
        ok(sap.SetModelIsLocked(False), "SetModelIsLocked")
    update_rows(sap, COEFF_TABLE, changes, "Name")
    got = {r["Name"]: r["C"] for r in read_table(sap, COEFF_TABLE)[2]}
    if any(abs(float(got[n]) - float(c["C"])) > 1e-9 for n, c in changes.items()):
        raise GenError("Calibrarea coeficientului seismic nu s-a aplicat (modelul a rămas blocat?).")
    return (f"forțe statice calibrate: T1x = {t1['X']:.3f} s (C = {coefficient_for_period(t1['X'], p):g}), "
            f"T1y = {t1['Y']:.3f} s (C = {coefficient_for_period(t1['Y'], p):g})")
