"""Elementele unui nivel al turnului in Y (calcule pure): pereti, stalpi, grinzi, placi, conturul exterior."""
from __future__ import annotations

from dataclasses import dataclass, field

from .geometry import WINGS, Pt, TowerGeom


@dataclass
class Wall:
    a: Pt
    b: Pt
    pier: str


@dataclass
class Beam:
    a: Pt
    b: Pt
    kind: str                       # perim | tip | cross | ray | door
    wing: int = -1


@dataclass
class StoryPlan:
    walls: list[Wall] = field(default_factory=list)
    columns: list[Pt] = field(default_factory=list)
    beams: list[Beam] = field(default_factory=list)
    slabs: list[tuple[Pt, ...]] = field(default_factory=list)
    outline: list[tuple[Pt, Pt]] = field(default_factory=list)          # muchiile conturului exterior, antiorar

    def extents(self) -> tuple[float, float]:
        """(latimea pe X, latimea pe Y) a conturului: latimea proiectata pentru vant."""
        pts = [p for e in self.outline for p in e]
        if not pts:
            pts = [p for w in self.walls for p in (w.a, w.b)]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return max(xs) - min(xs), max(ys) - min(ys)


def _segments(points: list[Pt]) -> list[tuple[Pt, Pt]]:
    return list(zip(points, points[1:]))


def story_plan(g: TowerGeom, bays: tuple[int, int, int]) -> StoryPlan:
    """Planul unui nivel cu `bays[w]` travei active pe aripa w (miezul si zona de legatura sunt mereu prezente)."""
    sp = StoryPlan()
    a, c, w2, half_face = g.apothem, g.corridor, g.half_width, g.radius / 2
    cols: dict[Pt, None] = {}
    for w in range(WINGS):
        nb = bays[w]
        L = lambda u, v, w=w: g.glob(w, u, v)               # noqa: E731
        st = [g.station(j) for j in range(nb + 1)]
        for s, side in ((1, "L"), (-1, "R")):
            line = [L(a, s * c)] + [L(u, s * c) for u in st]
            sp.walls += [Wall(p, q, f"SP{w}{side}") for p, q in _segments(line)]                       # perete de coridor, de la miez la varful aripii
            sp.walls.append(Wall(L(a, s * c), L(a, s * half_face), f"CORE{2 * w}{side}"))                # ciotul fetei miezului dintre coridor si colt
            sp.beams += [Beam(p, q, "perim", w) for p, q in _segments([L(u, s * w2) for u in st])]
        sp.beams.append(Beam(L(a, -c), L(a, c), "door", w))                                              # buiandrug deasupra intrarii in miez
        for j, u in enumerate(st):
            kind = "tip" if j == nb else "cross"
            vs = (-w2, -c, c, w2)
            sp.beams += [Beam(L(u, v0), L(u, v1), kind, w) for v0, v1 in zip(vs, vs[1:])]
            for s in (1, -1):
                cols[L(u, s * w2)] = None
        for j in range(nb):                                                                              # planseu: 3 fasii pe travee
            u0, u1 = st[j], st[j + 1]
            for v0, v1 in ((-w2, -c), (-c, c), (c, w2)):
                sp.slabs.append((L(u0, v0), L(u1, v0), L(u1, v1), L(u0, v1)))
        u0 = st[0]                                                                                        # zona de legatura cu miezul
        sp.slabs.append((L(a, -c), L(u0, -c), L(u0, c), L(a, c)))
        sp.slabs.append((L(a, c), L(u0, c), L(u0, w2), g.face_center(g.notch_face(w)), L(a, half_face)))
        sp.slabs.append((L(a, -half_face), g.face_center((2 * w - 1) % 6), L(u0, -w2), L(u0, -c), L(a, -c)))
        out = [L(st[0], -w2)] + [L(u, -w2) for u in st[1:]] + [L(st[-1], -c), L(st[-1], c), L(st[-1], w2)] + [L(u, w2) for u in reversed(st[:-1])]
        sp.outline += _segments(out)
        sp.beams.append(Beam(g.face_center(g.notch_face(w)), g.notch(w), "ray", w))
    for i in range(1, 6, 2):                                                                              # fetele spre crestaturi: pereti intregi, in doua la mijloc
        v0, v1 = g.face_ends(i)
        mid = g.face_center(i)
        sp.walls += [Wall(v0, mid, f"CORE{i}"), Wall(mid, v1, f"CORE{i}")]
    sp.columns = list(cols)
    return sp
