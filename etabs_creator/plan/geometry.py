"""Operatii pure pe multimi de celule: noduri si muchii."""
from __future__ import annotations

Cells = set[tuple[int, int]]


def nodes_of(cells: Cells) -> set[tuple[int, int]]:
    """Nodurile (ix, iy) ale colturilor celulelor."""
    return {(i + a, j + b) for i, j in cells for a in (0, 1) for b in (0, 1)}


def edges_of(cells: Cells) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    """(muchii pe X (iy, i), muchii pe Y (ix, j)) ale celulelor."""
    xe, ye = set(), set()
    for i, j in cells:
        xe |= {(j, i), (j + 1, i)}
        ye |= {(i, j), (i + 1, j)}
    return xe, ye


def adjacent_cells(axis: str, line: int, bay: int) -> Cells:
    """Celulele alaturate unui segment de grila: pe X (linia iy, deschiderea i) -> (i, iy-1) si (i, iy); pe Y (linia ix, traveea j) -> (ix-1, j) si (ix, j)."""
    return {(bay, line - 1), (bay, line)} if axis == "X" else {(line - 1, bay), (line, bay)}


def segment_nodes(axis: str, line: int, bay: int) -> set[tuple[int, int]]:
    """Capetele (ix, iy) ale unui segment de grila."""
    return {(bay, line), (bay + 1, line)} if axis == "X" else {(line, bay), (line, bay + 1)}
