"""Numarul de moduri: cerinta pe etaj se aplica etajelor PESTE TEREN (subsolul rigid nu vibreaza)."""
from __future__ import annotations

from ..connect import ok
from ..plan.towers import above_count


def modes_needed(spec) -> int:
    return spec.modes_per_story * (above_count(spec) + (spec.shell_stories if spec.opera else 0))


def apply_modal(sap, spec) -> str:
    n = modes_needed(spec)
    if spec.modal_type == "ritz":                       # cazul „Modal” devine Ritz cu pornire din acceleratiile UX, UY, UZ (cicluri 0, tinta 99 %)
        ritz = sap.LoadCases.ModalRitz
        ok(ritz.SetCase("Modal"), "ModalRitz.SetCase")
        ok(ritz.SetLoads("Modal", 2, ["Accel"] * 2, ["UX", "UY"], [0, 0], [99.0] * 2), "ModalRitz.SetLoads")      # masa verticala nu e in sursa de masa: UZ ar fi nul
        ok(ritz.SetNumberModes("Modal", n, 1), "ModalRitz.SetNumberModes")
        return f"moduri: {n} vectori Ritz (pornire din acceleratiile UX, UY; {spec.modes_per_story}/etaj peste teren)"
    ok(sap.LoadCases.ModalEigen.SetNumberModes("Modal", n, 1), "SetNumberModes")
    return f"moduri: {n} ({spec.modes_per_story}/etaj peste teren)"
