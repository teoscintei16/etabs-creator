"""Starea comuna a constructiei unui model: obiectele create (pentru reguli si restrangeri) si contoarele."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..connect import ok

# constante ETABS
CONCRETE_TYPE, SLAB, SHELL_THIN, SUPER_DEAD, OTHER = 2, 0, 1, 2, 8
SLAB_DIR_GRAVITY = 10                       # directia de incarcare „Gravity”
LOCAL_3 = 3                                 # axa locala 3 (normala la perete)
BELT_H = 0.25                               # m, inaltimea centurii dummy
SOIL_PATTERN = "Impingere_pamant"


@dataclass
class Ctx:
    sap: object
    spec: object
    plan: object
    sec: dict[str, str]
    xs: list[float]
    ys: list[float]
    count: dict[str, int] = field(default_factory=lambda: {"stalpi": 0, "grinzi": 0, "placi": 0})
    base_points: list[str] = field(default_factory=list)
    frames: list[str] = field(default_factory=list)         # bare cu zone rigide (fara centuri)
    beams: list[str] = field(default_factory=list)          # grinzi + centuri + grinzi de cuplare (insertie sus-centru)
    soil_areas: list[tuple[str, str, str]] = field(default_factory=list)      # (arie, axa, parte)
    spandrels: set[str] = field(default_factory=set)

    def bump(self, key: str, n: int = 1) -> None:
        self.count[key] = self.count.get(key, 0) + n

    def add_frame(self, a, b, prop: str, what: str) -> str:
        return ok(self.sap.FrameObj.AddByCoord(a[0], a[1], a[2], b[0], b[1], b[2], "", prop), f"AddByCoord ({what})")[0]

    def add_panel(self, axis: str, line: int, bay: int, z0: float, z1: float, prop: str, what: str) -> tuple[str, list[float], list[float]]:
        """Panou vertical pe un segment de grila. Intoarce (nume, x[4], y[4]); ordinea punctelor da axa locala 3: pe X -> -y, pe Y -> +x."""
        xs, ys = self.xs, self.ys
        if axis == "X":
            y = ys[line]
            px, py = [xs[bay], xs[bay + 1], xs[bay + 1], xs[bay]], [y] * 4
        else:
            x = xs[line]
            px, py = [x] * 4, [ys[bay], ys[bay + 1], ys[bay + 1], ys[bay]]
        name = ok(self.sap.AreaObj.AddByCoord(4, px, py, [z0, z0, z1, z1], "", prop), f"AddByCoord ({what})")[-1]   # COM intoarce si tablourile X, Y, Z
        return name, px, py

    def restrain_panel_base(self, name: str) -> None:
        self.base_points += list(ok(self.sap.AreaObj.GetPoints(name), "AreaObj.GetPoints")[1][:2])
