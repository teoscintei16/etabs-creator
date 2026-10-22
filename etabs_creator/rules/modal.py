"""Numarul de moduri: cerinta pe etaj se aplica etajelor PESTE TEREN (subsolul rigid nu vibreaza)."""
from __future__ import annotations

from ..connect import ok
from ..plan.towers import above_count


def modes_needed(spec) -> int:
    return spec.modes_per_story * above_count(spec)


def apply_modal(sap, spec) -> str:
    n = modes_needed(spec)
    ok(sap.LoadCases.ModalEigen.SetNumberModes("Modal", n, 1), "SetNumberModes")
    return f"moduri: {n} ({spec.modes_per_story}/etaj peste teren)"
