"""Punctul de insertie al grinzilor si centurilor: cardinal 8 (sus, centru), cu fata superioara la nivelul placii."""
from __future__ import annotations

from ..tables import update_rows


def apply_beam_insertion(sap, beams: list[str]) -> str:
    n = update_rows(sap, "Frame Assignments - Insertion Point", {b: {"CardinalPt": "8 (Top Center)"} for b in beams}, "UniqueName")
    return f"grinzi/centuri cu punct de inserție sus-centru ({n})"
