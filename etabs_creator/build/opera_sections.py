"""Sectiunile cojilor: coaja (arie), coasta, grinda de picior, grinda frontala, legatura de coama."""
from __future__ import annotations

from ..connect import ok
from .context import SHELL_THIN, SLAB
from .sections import _cm

RIB, FOOT, RIM, TIE = (0.5, 1.0), (1.0, 2.0), (0.8, 1.4), (0.8, 1.2)       # (latime, inaltime) m


def opera_sections(sap, spec, material: str) -> dict[str, str]:
    names = {"shell": f"SHELL{_cm(spec.shell_t)}", "rib": f"RIB{_cm(RIB[0])}x{_cm(RIB[1])}", "foot": f"FOOT{_cm(FOOT[0])}x{_cm(FOOT[1])}",
             "rim": f"RIM{_cm(RIM[0])}x{_cm(RIM[1])}", "tie": f"TIE{_cm(TIE[0])}x{_cm(TIE[1])}"}
    ok(sap.PropArea.SetSlab(names["shell"], SLAB, SHELL_THIN, material, spec.shell_t), "SetSlab (coajă)")
    for key, (b, h) in (("rib", RIB), ("foot", FOOT), ("rim", RIM), ("tie", TIE)):
        ok(sap.PropFrame.SetRectangle(names[key], material, h, b), f"SetRectangle ({key})")
    return names
