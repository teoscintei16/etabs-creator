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
    slabs: list[str] = field(default_factory=list)          # numele placilor (pentru defecte)
    pier_areas: list[tuple[str, str]] = field(default_factory=list)   # (arie perete, eticheta Pier)
    skip_columns: set[tuple[int, int, int]] = field(default_factory=set)       # (nivel, ix, iy): stalpi omisi (ex. in interiorul salilor)
    skip_beams: set[tuple[int, str, int, int]] = field(default_factory=set)    # (nivel, "X"|"Y", linia, deschiderea): grinzi omise
    sec_all: dict | None = None                               # sectiuni multiple pe categorie (zone de inaltime), pentru fisurare
    group: str = ""                                           # grupul curent de constructie (etapizare): obiectele create primesc acest grup
    members: dict[str, list[tuple[str, str]]] = field(default_factory=dict)       # grup -> [(Frame|Area, nume)]
    waivers: list = field(default_factory=list)               # (cheie de constatare, justificare): constatari asteptate, scrise in setarile verificatorului
    extra_combos: list = field(default_factory=list)          # combinatii suplimentare [(nume, [(caz, factor)])]
    variable: list[str] = field(default_factory=list)       # tipare variabile suplimentare (vant, temperatura): intra in combinatii

    def bump(self, key: str, n: int = 1) -> None:
        self.count[key] = self.count.get(key, 0) + n

    def _track(self, kind: str, name: str) -> str:
        if self.group:
            self.members.setdefault(self.group, []).append((kind, name))
        return name

    def add_frame(self, a, b, prop: str, what: str) -> str:
        return self._track("Frame", ok(self.sap.FrameObj.AddByCoord(a[0], a[1], a[2], b[0], b[1], b[2], "", prop), f"AddByCoord ({what})")[0])

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

    def add_poly(self, pts: list[tuple[float, float, float]], prop: str, what: str) -> str:
        """Arie cu oricate colturi (x, y, z), in ordinea data; intoarce numele."""
        return self._track("Area", ok(self.sap.AreaObj.AddByCoord(len(pts), [p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts], "", prop),
                                      f"AddByCoord ({what})")[-1])

    def restrain_panel_base(self, name: str) -> None:
        self.base_points += list(ok(self.sap.AreaObj.GetPoints(name), "AreaObj.GetPoints")[1][:2])
