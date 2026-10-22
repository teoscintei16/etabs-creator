"""Planul constructiei (calcule pure, fara ETABS): niveluri, turnuri, celule active pe nivel, pereti, grinzi de cuplare, subsol.

Grila totala are `bays+1` linii pe X (indice ix) si `travei+1` pe Y (iy). O celula (i, j) e dreptunghiul dintre liniile i..i+1 si j..j+1.
Un perete paralel cu X pe linia iy ocupa deschiderea i; unul paralel cu Y pe linia ix ocupa traveea j. Nivelurile sunt de jos in sus."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import basement as bsm
from .cells import check_shape, tower_cells, tower_voids
from .geometry import Cells, adjacent_cells, edges_of, nodes_of, segment_nodes
from .stories import Story, stories_of
from .towers import Tower, above_count, towers_of
from .walls import tower_coupling, tower_runs


@dataclass
class Plan:
    spec: object
    stories: list[Story]
    towers: list[Tower]
    cells: list[Cells]                                      # celule active pe nivel (union pe turnuri; subsol = grila completa)
    tower_cells: list[list[Cells]]                          # [turn][nivel] celulele turnului
    voids: Cells
    runs: list[dict]                                        # pereti (siruri de deschideri) cu eticheta Pier
    coupling: set[tuple[str, int, int]] = field(default_factory=set)
    prefix_of: dict[tuple[str, int, int], str] = field(default_factory=dict)

    # ---- subsol
    def is_basement(self, idx: int) -> bool:
        return self.stories[idx].basement

    def basement_walls(self, idx: int) -> list[dict]:
        """Peretii perimetrali ai subsolului, fara cei care coincid cu un perete al unui turn (acolo ramane peretele turnului, cu eticheta Pier)."""
        if not self.is_basement(idx):
            return []
        taken = {(w["axis"], w["line"], w["bay"]) for w in self.wall_panels(idx)}
        return [w for w in bsm.wall_panels(self.spec.bays, self.spec.travei) if (w["axis"], w["line"], w["bay"]) not in taken]

    # ---- pereti peste teren
    def _first_above(self) -> int:
        return next(i for i, s in enumerate(self.stories) if not s.basement)

    def wall_panels(self, idx: int) -> list[dict]:
        """[{"axis", "line", "bay", "pier"}] ale nivelului idx, doar unde segmentul e alipit de o celula activa a turnului lui.
        Peretii turnului continua in subsol (sub amprenta turnului la parter), cu aceeasi eticheta Pier."""
        out = []
        ref = self._first_above() if self.is_basement(idx) else idx
        for r in self.runs:
            cells = self.tower_cells[r["tower"] - 1][ref]
            for b in r["bays"]:
                if adjacent_cells(r["axis"], r["line"], b) & cells:
                    out.append({"axis": r["axis"], "line": r["line"], "bay": b, "pier": r["pier"]})
        return out

    def coupling_beams(self, idx: int) -> list[dict]:
        """[{"axis", "line", "bay", "spandrel"}] ale nivelului idx."""
        if self.is_basement(idx):
            return []
        out = []
        for axis, line, b in sorted(self.coupling):
            if adjacent_cells(axis, line, b) & self.cells[idx]:
                out.append({"axis": axis, "line": line, "bay": b, "spandrel": f"{self.prefix_of[(axis, line, b)]}SP{axis}{line}_{b}"})
        return out

    # ---- cadre
    def _replaced(self, idx: int) -> tuple[set, set]:
        """Muchiile de grinda inlocuite de pereti, grinzi de cuplare si (la subsol) de peretii perimetrali."""
        xs, ys = set(), set()
        for w in self.wall_panels(idx) + self.coupling_beams(idx):
            (xs if w["axis"] == "X" else ys).add((w["line"], w["bay"]))
        if self.is_basement(idx):
            px, py = bsm.perimeter_edges(self.spec.bays, self.spec.travei)
            xs |= px
            ys |= py
        return xs, ys

    def beams(self, idx: int) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
        """(grinzi pe X (iy, i), grinzi pe Y (ix, j)) ale nivelului, fara cele inlocuite de pereti."""
        if not self.spec.gravity_frame and not self.is_basement(idx):
            return [], []
        xe, ye = edges_of(self.cells[idx])
        rx, ry = self._replaced(idx)
        return sorted(xe - rx), sorted(ye - ry)

    def columns(self, idx: int) -> list[tuple[int, int]]:
        """Nodurile cu stalp pe nivelul idx: noduri folosite de celulele nivelului sau ale celor de deasupra, fara capetele de pereti
        (si fara perimetrul subsolului, unde sunt peretii)."""
        if not self.spec.gravity_frame and not self.is_basement(idx):
            return []
        used: set[tuple[int, int]] = set()
        for c in self.cells[idx:]:
            used |= nodes_of(c)
        skip: set[tuple[int, int]] = set()
        for w in self.wall_panels(idx) + self.coupling_beams(idx):
            skip |= segment_nodes(w["axis"], w["line"], w["bay"])
        if self.is_basement(idx):
            skip |= bsm.perimeter_nodes(self.spec.bays, self.spec.travei)
        return sorted(used - skip)

    def slab_cells(self, idx: int) -> list[tuple[int, int]]:
        return sorted(self.cells[idx] - (set() if self.is_basement(idx) else self.voids))


def build_plan(spec) -> Plan:
    towers = towers_of(spec)
    for t in towers:
        check_shape(spec, t)
    n_above = above_count(spec)
    stories = stories_of(spec, n_above)
    full = {(i, j) for i in range(spec.bays) for j in range(spec.travei)}
    cells: list[Cells] = []
    per_tower: list[list[Cells]] = [[] for _ in towers]
    above = 0
    for st in stories:
        if st.basement:
            cells.append(set(full))
            for t in per_tower:
                t.append(set())
            continue
        above += 1
        union: Cells = set()
        for k, tw in enumerate(towers):
            c = tower_cells(spec, tw, above)
            per_tower[k].append(c)
            union |= c
        cells.append(union)
    voids: Cells = set()
    runs: list[dict] = []
    coupling: set[tuple[str, int, int]] = set()
    prefix_of: dict[tuple[str, int, int], str] = {}
    for tw in towers:
        voids |= tower_voids(spec, tw)
        r = tower_runs(spec, tw)
        runs += r
        c = tower_coupling(spec, tw, r)
        coupling |= c
        prefix_of.update({key: tw.prefix for key in c})
    return Plan(spec, stories, towers, cells, per_tower, voids, runs, coupling, prefix_of)
