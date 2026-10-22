"""Actiunea seismica in model: functia spectrala P100-1, cazurile de spectru SPECX/SPECY si 4 tipare statice cu excentricitate ±."""
from __future__ import annotations

from ..connect import GenError, ok
from ..seismic import params_from, seismic_coefficient, spectrum_points
from ..tables import upsert_entities

QUAKE = 5
RS_FUNCTION = "SPECTRU_P100"
STATIC = (("EXP", "X", "Plus"), ("EXN", "X", "Minus"), ("EYP", "Y", "Plus"), ("EYN", "Y", "Minus"))
COEFF_TABLE = "Load Pattern Definitions - Auto Seismic - User Coefficient"


def apply_seismic(sap, spec, top_story: str, base_story: str = "Base") -> tuple[list[str], list[str], list[str]]:
    """Intoarce (tipare statice, cazuri de spectru, note). Cazurile de spectru: 100 % + 30 %, CQC, SRSS, excentricitate."""
    p = params_from(spec)
    pts = spectrum_points(p)
    rows = [dict(Name=RS_FUNCTION, Period=f"{t:g}", Value=f"{v:g}", DampRatio=f"{p.damping:g}" if i == 0 else "") for i, (t, v) in enumerate(pts)]
    upsert_entities(sap, "Functions - Response Spectrum - User Defined", "Name", rows)
    rs = sap.LoadCases.ResponseSpectrum
    cases = []
    for name, main, other in (("SPECX", "U1", "U2"), ("SPECY", "U2", "U1")):
        ok(rs.SetCase(name), "ResponseSpectrum.SetCase")
        ok(rs.SetLoads(name, 2, [main, other], [RS_FUNCTION, RS_FUNCTION], [1.0, p.orth], ["Global", "Global"], [0.0, 0.0]), "ResponseSpectrum.SetLoads")
        ok(rs.SetModalCase(name, "Modal"), "SetModalCase")
        ok(rs.SetEccentricity(name, p.ecc), "SetEccentricity")
        cases.append(name)
    spec_rows, patterns = [], []
    for name, d, e in STATIC:
        r = sap.LoadPatterns.Add(name, QUAKE, 0, True)             # intai tiparul (API), apoi coeficientul (tabel): invers nu se creeaza
        if r != 0:
            raise GenError(f"Nu pot crea tiparul {name} (cod {r}).")
        flags = {f"{ax}Dir{kind}": "No" for ax in "XY" for kind in ("", "PlusE", "MinusE")}
        flags[f"{d}Dir{e}E"] = "Yes"
        spec_rows.append(dict(Name=name, IsAuto="No", EccRatio=f"{p.ecc:g}", TopStory=top_story, BotStory=base_story,
                              C=f"{seismic_coefficient(p):g}", K="1", **flags))
        patterns.append(name)
    upsert_entities(sap, COEFF_TABLE, "Name", spec_rows)
    return patterns, cases, [f"spectru P100-1 ({len(pts)} puncte), C = {seismic_coefficient(p):g}, e = {p.ecc:g}"]
