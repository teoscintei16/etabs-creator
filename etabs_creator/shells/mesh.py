"""Reteaua cojii: noduri [i][j] (i = de-a lungul coastelor din A, j = peste coaste), fete (patrulatere) si muchii."""
from __future__ import annotations

from dataclasses import dataclass

from .sphere import point_on, s_for_base_y, sphere_center
from .vec import V3


@dataclass
class ShellMesh:
    name: str
    a: V3
    b: V3
    c: V3
    center: V3
    radius: float
    nodes: list[list[V3]]               # nodes[i][j], i = 0..n (i = 0: varful A), j = 0..m (j = 0: coasta de baza AB)

    @property
    def n(self) -> int:
        return len(self.nodes) - 1

    @property
    def m(self) -> int:
        return len(self.nodes[0]) - 1

    def faces(self) -> list[tuple[V3, ...]]:
        """Patrulaterele retelei (varful evantaiului e taiat: primul rand are latime). Ordinea colturilor da normala spre exterior."""
        out: list[tuple[V3, ...]] = []
        for i in range(self.n):
            for j in range(self.m):
                p00, p01, p10, p11 = self.nodes[i][j], self.nodes[i][j + 1], self.nodes[i + 1][j], self.nodes[i + 1][j + 1]
                out.append((p00, p10, p11, p01))
        return out

    def base_nodes(self) -> list[V3]:
        """Nodurile coastei de baza (AB), de la A la B."""
        return [self.nodes[i][0] for i in range(self.n + 1)]

    def rib(self, j: int) -> list[V3]:
        return [self.nodes[i][j] for i in range(self.n + 1)]

    def rim(self) -> list[V3]:
        """Muchia frontala BC (ultimul rand), de la B la C."""
        return list(self.nodes[self.n])

    def side(self) -> list[V3]:
        """Muchia AC (ultima coasta)."""
        return self.rib(self.m)

    def max_z(self) -> float:
        return max(p[2] for row in self.nodes for p in row)


def build_mesh(name: str, a: V3, b: V3, c: V3, radius: float, dy: float, across: int, tip_cut: float = 6.0) -> ShellMesh:
    """Reteaua cojii: petec de sfera cu baza „indreptata” (fiecare rand se muta pe orizontala cu sageata arcului de baza, ≤ ~4 m, ca baza sa fie pe
    peretele de pe linia grilei; muchia frontala BC ramane exact pe sfera). Randurile sunt alese astfel incat nodurile coastei de baza sa fie la pas `dy` in y (coincid cu liniile grilei podiumului);
    varful A al evantaiului e taiat pe `tip_cut` m (piedestalul), ca primul rand sa aiba latime si elementele sa nu degenereze."""
    center = sphere_center(a, b, c, radius)
    n = max(round(abs(b[1] - a[1]) / dy), 3)
    k0 = min(max(round(tip_cut / dy), 1), n - 2)
    ys = [a[1] + (b[1] - a[1]) * i / n for i in range(n + 1)]
    ss = [s_for_base_y(center, radius, a, b, c, y) for y in ys[k0:-1]] + [1.0]
    nodes = [[point_on(center, radius, a, b, c, s, j / across) for j in range(across + 1)] for s in ss]
    out = []
    for row, y in zip(nodes, ys[k0:]):
        shift = a[0] - row[0][0]                                # arcul de baza e curb in plan (sageata ≤ cativa m): fiecare rand se deplaseaza
        pts = [(round(p[0] + shift, 3), round(p[1], 3), round(p[2], 3)) for p in row]     # pe orizontala ca baza sa cada pe linia grilei
        pts[0] = (a[0], round(y, 3), a[2])                      # coasta de baza: exact pe linia grilei, la cota podiumului
        out.append(pts)
    return ShellMesh(name, a, b, c, center, radius, out)
