"""Nuclee de pereti in forma de L, C, I, H, T, desenate pe liniile grilei.

Un nucleu ocupa un dreptunghi de celule (ci0, cj0, cnx, cny) din turn. Fiecare perete drept e o „rula” (axa, linia, deschiderile):
  L: perete pe X la baza (y = cj0) + perete pe Y la stanga (x = ci0)
  C: pereti pe X sus si jos (y = cj0, cj0+cny) + perete pe Y la stanga (x = ci0)
  I: pereti pe X sus si jos + inima pe Y la mijloc (x = ci0 + cnx//2)           (cere cnx ≥ 2)
  H: pereti pe Y stanga si dreapta + inima pe X la mijloc (y = cj0 + cny//2)    (cere cny ≥ 2)
  T: perete pe X sus (y = cj0+cny) + inima pe Y la mijloc (x = ci0 + cnx//2)    (cere cnx ≥ 2)"""
from __future__ import annotations

from ..connect import GenError

NEEDS = {"I": (2, 1), "H": (1, 2), "T": (2, 1), "L": (1, 1), "C": (1, 1)}      # (cnx minim, cny minim)


def core_rect(text: str, nx: int, ny: int) -> tuple[int, int, int, int]:
    """(ci0, cj0, cnx, cny) din „i0,j0,nx,ny” sau, daca e gol, un dreptunghi centrat de ~jumatate din plan (cel putin 2×2)."""
    if not text.strip():
        cnx, cny = min(nx, max(2, nx // 2)), min(ny, max(2, ny // 2))
        return (nx - cnx) // 2, (ny - cny) // 2, cnx, cny
    try:
        ci0, cj0, cnx, cny = (int(x) for x in text.split(","))
    except ValueError as e:
        raise GenError(f"Nucleu „{text}”: folosește formatul i0,j0,nx,ny.") from e
    if not (ci0 >= 0 and cj0 >= 0 and cnx >= 1 and cny >= 1 and ci0 + cnx <= nx and cj0 + cny <= ny):
        raise GenError(f"Nucleu „{text}”: dreptunghiul iese din turn ({nx}×{ny} celule).")
    return ci0, cj0, cnx, cny


def core_runs(shape: str, text: str, nx: int, ny: int) -> list[tuple[str, int, list[int]]]:
    """[(axa, linia, deschiderile)] ale nucleului, in coordonatele locale ale turnului."""
    if not shape:
        return []
    ci0, cj0, cnx, cny = core_rect(text, nx, ny)
    need_x, need_y = NEEDS[shape]
    if cnx < need_x or cny < need_y:
        raise GenError(f"Nucleul {shape} cere cel puțin {need_x}×{need_y} celule (are {cnx}×{cny}).")
    xb, yb = list(range(ci0, ci0 + cnx)), list(range(cj0, cj0 + cny))        # deschiderile pe X si traveile pe Y ocupate
    mid_x, mid_y = ci0 + cnx // 2, cj0 + cny // 2
    lo_y, hi_y, lo_x, hi_x = cj0, cj0 + cny, ci0, ci0 + cnx
    if shape == "L":
        return [("X", lo_y, xb), ("Y", lo_x, yb)]
    if shape == "C":
        return [("X", lo_y, xb), ("X", hi_y, xb), ("Y", lo_x, yb)]
    if shape == "I":
        return [("X", lo_y, xb), ("X", hi_y, xb), ("Y", mid_x, yb)]
    if shape == "H":
        return [("Y", lo_x, yb), ("Y", hi_x, yb), ("X", mid_y, xb)]
    return [("X", hi_y, xb), ("Y", mid_x, yb)]                                # T
