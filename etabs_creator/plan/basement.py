"""Subsolul: planul complet al grilei, pereti perimetrali (panouri) si muchiile perimetrului."""
from __future__ import annotations


def perimeter_edges(bays: int, travei: int) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    """(muchii pe X (iy, i), muchii pe Y (ix, j)) de pe perimetrul grilei."""
    xe = {(j, i) for i in range(bays) for j in (0, travei)}
    ye = {(i, j) for j in range(travei) for i in (0, bays)}
    return xe, ye


def perimeter_nodes(bays: int, travei: int) -> set[tuple[int, int]]:
    return {(i, j) for i in range(bays + 1) for j in range(travei + 1) if i in (0, bays) or j in (0, travei)}


def wall_panels(bays: int, travei: int) -> list[dict]:
    """Panourile peretilor perimetrali: [{"axis", "line", "bay", "side": "lo"|"hi"}] (side = partea pamantului pe acea latura)."""
    out = [{"axis": "X", "line": j, "bay": i, "side": "lo" if j == 0 else "hi"} for j in (0, travei) for i in range(bays)]
    out += [{"axis": "Y", "line": i, "bay": j, "side": "lo" if i == 0 else "hi"} for i in (0, bays) for j in range(travei)]
    return out
