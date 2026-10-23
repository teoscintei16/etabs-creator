"""Retragerile in spirala: la anumite niveluri, pe rand, cate o aripa pierde o travee."""
from __future__ import annotations


def bays_at(spec, number: int) -> tuple[int, int, int]:
    """Numarul de travei active pe fiecare aripa la nivelul `number` (1..)."""
    bays = [spec.wing_bays] * 3
    if number < spec.setback_start:
        return tuple(bays)
    steps = (number - spec.setback_start) // spec.setback_every + 1
    w = 0
    for _ in range(steps):
        for _k in range(3):                              # urmatoarea aripa care mai are travei
            if bays[w % 3] > 0:
                bays[w % 3] -= 1
                w += 1
                break
            w += 1
        else:
            break
    return tuple(bays)


def setback_levels(spec, total: int) -> list[tuple[int, tuple[int, int, int]]]:
    """[(nivel, travei pe aripi)] la fiecare nivel la care geometria se schimba."""
    out, prev = [], None
    for n in range(1, total + 1):
        b = bays_at(spec, n)
        if b != prev:
            out.append((n, b))
            prev = b
    return out
