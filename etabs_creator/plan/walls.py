"""Peretii unui turn: pereti pe linii de grila + nucleu (L, C, I, H, T), unirea lor in „rule” (un perete drept = o eticheta Pier) si grinzile de cuplare."""
from __future__ import annotations

from collections import defaultdict

from .cores import core_runs
from .indices import groups, parse_indices
from .towers import Tower


def raw_runs(spec, tower: Tower) -> dict[tuple[str, int], set[int]]:
    """{(axa, linie): deschideri} in coordonatele LOCALE ale turnului, din liniile configurate si din nucleu."""
    out: dict[tuple[str, int], set[int]] = defaultdict(set)
    if not spec.walls:
        return out
    for axis, lines_txt, bays_txt, n_lines, n_bays in (("X", spec.wall_lines_x, spec.wall_bays_x, tower.ny + 1, tower.nx),
                                                       ("Y", spec.wall_lines_y, spec.wall_bays_y, tower.nx + 1, tower.ny)):
        lines = parse_indices(lines_txt, n_lines, f"Pereți pe {axis}: linii", allow_none=True)
        bays = parse_indices(bays_txt, n_bays, f"Pereți pe {axis}: deschideri", allow_none=True)
        for line in lines:
            out[(axis, line)] |= set(bays)
    for axis, line, bays in core_runs(spec.core_shape, spec.core_cells, tower.nx, tower.ny):
        out[(axis, line)] |= set(bays)
    return out


def tower_runs(spec, tower: Tower) -> list[dict]:
    """[{"axis", "line", "bays", "pier"}] in coordonatele grilei totale. Eticheta Pier = „PX1”, „PY2”… (cu prefix „T2_” la mai multe turnuri)."""
    runs: list[dict] = []
    counter = {"X": 0, "Y": 0}
    for (axis, line), bays in sorted(raw_runs(spec, tower).items(), key=lambda kv: (kv[0][0], kv[0][1])):
        for g in groups(sorted(bays)):
            counter[axis] += 1
            if axis == "X":
                gl, gb = line + tower.j0, [b + tower.i0 for b in g]
            else:
                gl, gb = line + tower.i0, [b + tower.j0 for b in g]
            runs.append({"axis": axis, "line": gl, "bays": gb, "pier": f"{tower.prefix}P{axis}{counter[axis]}", "tower": tower.index})
    return runs


def tower_coupling(spec, tower: Tower, runs: list[dict]) -> set[tuple[str, int, int]]:
    """{(axa, linie, deschidere)} cu grinda de cuplare: deschiderile alese care nu sunt pereti, pe liniile cu pereti ale turnului."""
    out: set[tuple[str, int, int]] = set()
    for axis, txt, n_bays, off in (("X", spec.coupling_bays_x, tower.nx, tower.i0), ("Y", spec.coupling_bays_y, tower.ny, tower.j0)):
        if not str(txt).strip():
            continue
        wall_lines = {r["line"] for r in runs if r["axis"] == axis}
        for b in parse_indices(txt, n_bays, f"Grinzi de cuplare pe {axis}: deschideri"):
            gb = b + off
            for line in wall_lines:
                if not any(r["axis"] == axis and r["line"] == line and gb in r["bays"] for r in runs):
                    out.add((axis, line, gb))
    return out
