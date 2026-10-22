"""Reteaua radiala a unui plan liber: inele de la centru la contur, cu noduri, fete (placi), muchii (grinzi).

Nod = (r, j): inelul r (0..n) si punctul j al conturului. Daca atriul e 0, inelul 0 e un singur nod (centrul, j = 0);
altfel inelul 0 e conturul golului central, la scara `atrium`."""
from __future__ import annotations

from dataclasses import dataclass

Node = tuple[int, int]
Pt = tuple[float, float]


@dataclass
class Radial:
    boundary: list[Pt]
    rings: int
    atrium: float

    @property
    def m(self) -> int:
        return len(self.boundary)

    def scale(self, r: int) -> float:
        return self.atrium + (1.0 - self.atrium) * r / self.rings

    def nodes(self) -> list[Node]:
        out: list[Node] = [(0, 0)] if self.atrium == 0 else [(0, j) for j in range(self.m)]
        for r in range(1, self.rings + 1):
            out += [(r, j) for j in range(self.m)]
        return out

    def xy(self, node: Node) -> Pt:
        r, j = node
        if r == 0 and self.atrium == 0:
            return 0.0, 0.0
        s = self.scale(r)
        x, y = self.boundary[j % self.m]
        return x * s, y * s

    def faces(self) -> list[tuple[Node, ...]]:
        """Fetele in sens trigonometric: triunghiuri la centru (atriu 0), patrulatere intre inele."""
        out: list[tuple[Node, ...]] = []
        for j in range(self.m):
            j2 = (j + 1) % self.m
            for r in range(1, self.rings + 1):
                if r == 1 and self.atrium == 0:
                    out.append(((0, 0), (1, j), (1, j2)))
                else:
                    out.append(((r - 1, j), (r, j), (r, j2), (r - 1, j2)))
        return out

    def edges(self) -> list[tuple[Node, Node, str]]:
        """Muchiile grinzilor: (nod, nod, tip) cu tip „ring” (pe inel, inclusiv conturul) sau „radial”."""
        out: list[tuple[Node, Node, str]] = []
        for j in range(self.m):
            j2 = (j + 1) % self.m
            for r in range(0 if self.atrium else 1, self.rings + 1):
                out.append(((r, j), (r, j2), "ring"))
            for r in range(1, self.rings + 1):
                a = (0, 0) if (r == 1 and self.atrium == 0) else (r - 1, j)
                out.append((a, (r, j), "radial"))
        return out

    def boundary_edge(self, j: int) -> tuple[Node, Node]:
        return (self.rings, j % self.m), (self.rings, (j + 1) % self.m)
