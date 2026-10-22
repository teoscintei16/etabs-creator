"""Celulele active ale unui turn la fiecare etaj (forma in plan: dreptunghi, L, retragere) si golurile din plansee."""
from __future__ import annotations

from ..connect import GenError
from .towers import Tower


def check_shape(spec, tower: Tower) -> None:
    if spec.shape == "L" and not (1 <= spec.cut_bays < tower.nx and 1 <= spec.cut_travei < tower.ny):
        raise GenError(f"Forma L cere 1 ≤ deschideri tăiate < {tower.nx} și 1 ≤ travei tăiate < {tower.ny} (turnul {tower.index}).")
    if spec.shape == "setback" and not (1 <= spec.setback_story < tower.stories and 1 <= spec.setback_bays < tower.nx):
        raise GenError(f"Retragerea cere 1 ≤ etaj < {tower.stories} și 1 ≤ deschideri eliminate < {tower.nx} (turnul {tower.index}).")


def local_cells(spec, tower: Tower, above: int) -> set[tuple[int, int]]:
    """Celulele turnului (coordonate locale) la etajul `above` (1..tower.stories)."""
    cells = {(i, j) for i in range(tower.nx) for j in range(tower.ny)}
    if spec.shape == "L":
        return {(i, j) for i, j in cells if not (i >= tower.nx - spec.cut_bays and j >= tower.ny - spec.cut_travei)}
    if spec.shape == "setback" and above > spec.setback_story:
        return {(i, j) for i, j in cells if i < tower.nx - spec.setback_bays}
    return cells


def tower_cells(spec, tower: Tower, above: int) -> set[tuple[int, int]]:
    """Celulele active ale turnului la etajul `above`, in coordonatele grilei totale (gol daca turnul e mai scund)."""
    if above > tower.stories:
        return set()
    return {(tower.i0 + i, tower.j0 + j) for i, j in local_cells(spec, tower, above)}


def parse_cells(text: str, nx: int, ny: int) -> set[tuple[int, int]]:
    """„1,1;2,0” -> {(1, 1), (2, 0)} in coordonatele locale ale turnului (nx × ny celule)."""
    out = set()
    for tok in (t.strip() for t in str(text).split(";") if t.strip()):
        try:
            i, j = (int(x) for x in tok.split(","))
        except ValueError as e:
            raise GenError(f"Gol în planșeu „{tok}”: folosește formatul i,j (ex. 1,1;2,0).") from e
        if not (0 <= i < nx and 0 <= j < ny):
            raise GenError(f"Gol în planșeu „{tok}”: celula nu există (i între 0 și {nx - 1}, j între 0 și {ny - 1}).")
        out.add((i, j))
    return out


def tower_voids(spec, tower: Tower) -> set[tuple[int, int]]:
    """Golurile din plansee ale turnului, in coordonatele grilei totale."""
    if not spec.void_cells.strip():
        return set()
    return {(tower.i0 + i, tower.j0 + j) for i, j in parse_cells(spec.void_cells, tower.nx, tower.ny)}
