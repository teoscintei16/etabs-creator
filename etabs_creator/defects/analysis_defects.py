"""Defecte de analiza: moduri putine, caz Ritz fara accelerații, grade de libertate dezactivate."""
from __future__ import annotations

from ..connect import ok
from .registry import defect


@defect("modes_few", "caz modal cu doar 4 moduri")
def modes_few(c) -> str:
    ok(c.sap.LoadCases.ModalEigen.SetNumberModes("Modal", 4, 1), "SetNumberModes")
    return "moduri: doar 4"


@defect("ritz_no_accel", "caz Ritz cu vector de pornire doar pe Z")
def ritz_no_accel(c) -> str:
    ok(c.sap.LoadCases.ModalRitz.SetCase("RitzTest"), "ModalRitz.SetCase")
    ok(c.sap.LoadCases.ModalRitz.SetLoads("RitzTest", 1, ["Accel"], ["UZ"], [0], [99.0]), "ModalRitz.SetLoads")
    return "caz Ritz „RitzTest” fără accelerații pe X și Y"


@defect("dof_off", "UZ și RZ dezactivate")
def dof_off(c) -> str:
    ok(c.sap.Analyze.SetActiveDOF([True, True, False, True, True, False]), "SetActiveDOF")
    return "grade de libertate: UZ și RZ dezactivate"
