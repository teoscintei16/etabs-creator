"""Planul unei structuri cu plan liber (calcule pure): retea radiala + niveluri transformate + stalpi, grinzi, pereti, placi pe fiecare etaj."""
from __future__ import annotations

from dataclasses import dataclass

from ..connect import GenError
from ..plan.indices import groups
from ..plan.stories import Story, stories_of
from .levels import Level, story_levels
from .outline import outline
from .radial import Node, Radial

IDENTITY = Level()


def parse_wall_edges(text: str, m: int) -> list[int]:
    t = text.strip().lower()
    if t in ("", "none"):
        return []
    if t == "all":
        return list(range(m))
    if t == "alternate":
        return list(range(0, m, 2))
    out: set[int] = set()
    for tok in (x.strip() for x in t.split(",") if x.strip()):
        try:
            j = int(tok)
        except ValueError as e:
            raise GenError(f"Laturi cu pereți: „{tok}” nu e un indice (none, all, alternate sau 0,3,6).") from e
        if not 0 <= j < m:
            raise GenError(f"Latura {j} nu există (conturul are {m} laturi, 0..{m - 1}).")
        out.add(j)
    return sorted(out)


@dataclass
class FreePlan:
    spec: object
    stories: list[Story]
    radial: Radial
    wall_edges: list[int]
    piers: dict[int, str]                         # latura -> eticheta Pier (laturile consecutive au aceeasi eticheta)

    def is_basement(self, idx: int) -> bool:
        return self.stories[idx].basement

    def above_number(self, idx: int) -> int:
        """Numarul etajului peste teren (1..n) al nivelului idx."""
        return idx - sum(1 for s in self.stories if s.basement) + 1

    def levels(self, idx: int) -> tuple[Level, Level]:
        """(transformarea de jos, de sus) a etajului; subsolul are planul netransformat."""
        if self.is_basement(idx):
            return IDENTITY, IDENTITY
        return story_levels(self.spec, self.above_number(idx), self.spec.stories)

    def xy(self, node: Node, level: Level) -> tuple[float, float]:
        """Coordonatele nodului la un nivel, rotunjite la 1 mm (nodurile comune coincid exact; fara zecimale parazite pe curbe)."""
        x, y = level.apply(self.radial.xy(node))
        return round(x, 3) + 0.0, round(y, 3) + 0.0

    # ---- elemente pe nivel
    def wall_nodes(self, idx: int) -> set[Node]:
        out: set[Node] = set()
        for j in self.walled_edges(idx):
            out |= set(self.radial.boundary_edge(j))
        return out

    def walled_edges(self, idx: int) -> list[int]:
        """Laturile cu perete pe nivelul idx: in subsol toate (perimetral); peste teren cele alese."""
        return list(range(self.radial.m)) if self.is_basement(idx) else list(self.wall_edges)

    def wall_panels(self, idx: int) -> list[dict]:
        """Peretii turnului: [{"edge", "pier"}]; in subsol continua doar laturile alese (cu aceeasi eticheta), restul sunt pereti de subsol."""
        if self.is_basement(idx) and not self.spec.walls_through_basement:
            return []
        return [{"edge": j, "pier": self.piers[j]} for j in self.wall_edges]

    def basement_walls(self, idx: int) -> list[dict]:
        if not self.is_basement(idx):
            return []
        taken = {w["edge"] for w in self.wall_panels(idx)}
        return [{"edge": j} for j in range(self.radial.m) if j not in taken]

    def columns(self, idx: int) -> list[Node]:
        mode = self.spec.free_columns
        r = self.radial
        if self.is_basement(idx):
            nodes = [n for n in r.nodes() if n[0] < r.rings]                  # subsol: noduri interioare; perimetrul e perete
            skip = {n for j in range(r.m) for n in r.boundary_edge(j)}
        else:
            if mode == "none":
                return []
            nodes = [n for n in r.nodes() if mode == "all" or n[0] == r.rings]
            skip = self.wall_nodes(idx)
        return [n for n in nodes if n not in skip]

    def beams(self, idx: int) -> list[tuple[Node, Node, str]]:
        """Grinzile nivelului: toate muchiile retelei, fara laturile conturului inlocuite de pereti."""
        replaced = {frozenset(self.radial.boundary_edge(j)) for j in (range(self.radial.m) if self.is_basement(idx) else self.wall_edges)}
        return [(a, b, k) for a, b, k in self.radial.edges() if frozenset((a, b)) not in replaced]

    def slab_faces(self, idx: int) -> list[tuple[Node, ...]]:
        return self.radial.faces()


def build_free_plan(spec) -> FreePlan:
    boundary = outline(spec)
    radial = Radial(boundary, spec.free_rings, spec.atrium)
    wall_edges = parse_wall_edges(spec.free_wall_edges, radial.m)
    piers: dict[int, str] = {}
    for k, g in enumerate(groups(wall_edges), 1):
        for j in g:
            piers[j] = f"PW{k}"
    return FreePlan(spec, stories_of(spec, spec.stories), radial, wall_edges, piers)
