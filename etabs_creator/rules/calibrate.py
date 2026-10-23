"""Calibrarea fortelor statice: C = λ·Sd(T1)/g pe fiecare directie, dupa o analiza modala (ca un proiectant)."""
from __future__ import annotations

from ..connect import GenError, ok
from ..seismic import coefficient_for_period, params_from
from ..tables import read_display, read_table, update_rows
from .seismic import COEFF_TABLE, RS_FUNCTION

DYNAMIC_MIN = 0.85                        # P100-1: forta taietoare dinamica ≥ 0,85 din cea statica (altfel rezultatele spectrale se amplifica)
MARGIN = 1.01


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
    scales = dynamic_scales(sap, p, t1)
    changes = {f"E{ax}{sg}": {"C": f"{coefficient_for_period(t1[ax], p):g}"} for ax in ("X", "Y") for sg in ("P", "N")}
    if sap.GetModelIsLocked():
        ok(sap.SetModelIsLocked(False), "SetModelIsLocked")
    update_rows(sap, COEFF_TABLE, changes, "Name")
    got = {r["Name"]: r["C"] for r in read_table(sap, COEFF_TABLE)[2]}
    if any(abs(float(got[n]) - float(c["C"])) > 1e-9 for n, c in changes.items()):
        raise GenError("Calibrarea coeficientului seismic nu s-a aplicat (modelul a rămas blocat?).")
    note = apply_dynamic_scales(sap, p, scales)
    return (f"forțe statice calibrate: T1x = {t1['X']:.3f} s (C = {coefficient_for_period(t1['X'], p):g}), "
            f"T1y = {t1['Y']:.3f} s (C = {coefficient_for_period(t1['Y'], p):g})" + note)


def _peak(sap, case: str, field: str) -> float:
    db = sap.DatabaseTables
    db.SetLoadCasesSelectedForDisplay([case])
    db.SetLoadCombinationsSelectedForDisplay([])
    rows = read_display(sap, "Base Reactions")
    return max((abs(float(r[field])) for r in rows if r.get(field) not in (None, "")), default=0.0)


def dynamic_scales(sap, p, t1: dict[str, float]) -> dict[str, float]:
    """Factorul cu care se amplifica spectrul pe fiecare directie ca Fb dinamic sa fie ≥ 0,85 din Fb static (cu coeficientul C calibrat); 1 daca deja e."""
    out = {}
    coeff = {r["Name"]: float(r["C"]) for r in read_table(sap, COEFF_TABLE)[2]}
    for ax in ("X", "Y"):
        stat_old = _peak(sap, f"E{ax}P", f"F{ax}")
        dyn = _peak(sap, f"SPEC{ax}", f"F{ax}")
        c_old, c_new = coeff[f"E{ax}P"], coefficient_for_period(t1[ax], p)
        stat = stat_old * c_new / c_old if c_old else stat_old
        out[ax] = max(1.0, DYNAMIC_MIN * MARGIN * stat / dyn) if dyn > 0 else 1.0
    return out


def apply_dynamic_scales(sap, p, scales: dict[str, float]) -> str:
    """Rescrie factorii de scara ai cazurilor de spectru (SPECX, SPECY) si intoarce nota (gol daca nu s-a amplificat nimic)."""
    if all(abs(k - 1.0) < 1e-9 for k in scales.values()):
        return ""
    rs = sap.LoadCases.ResponseSpectrum
    for ax, main, other in (("X", "U1", "U2"), ("Y", "U2", "U1")):
        k = scales[ax]
        ok(rs.SetLoads(f"SPEC{ax}", 2, [main, other], [RS_FUNCTION, RS_FUNCTION], [k, p.orth * k], ["Global", "Global"], [0.0, 0.0]), "ResponseSpectrum.SetLoads (scară)")
    return f"; spectru amplificat ×{scales['X']:.2f} (X), ×{scales['Y']:.2f} (Y) pentru Fb dinamic ≥ {DYNAMIC_MIN:g} Fb static"
