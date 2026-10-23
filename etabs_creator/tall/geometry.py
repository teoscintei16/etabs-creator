"""Geometria planului in Y (calcule pure): miez hexagonal, trei aripi la 120°, puncte de crestatura, coordonate globale.

Coordonate locale pe aripa w: u de-a lungul axei (de la centru), v lateral (pozitiv spre stanga, antiorar). Aripa w are axa la 120°·w.
Fetele hexagonului au normalele la 60°·i; fata 2w priveste aripa w, fata 2w+1 priveste crestatura dintre aripile w si w+1."""
from __future__ import annotations

import math
from dataclasses import dataclass

Pt = tuple[float, float]
WINGS = 3


def rnd(p: Pt) -> Pt:
    """Rotunjire la 1 mm (nodurile comune coincid exact)."""
    return round(p[0], 3) + 0.0, round(p[1], 3) + 0.0


@dataclass(frozen=True)
class TowerGeom:
    radius: float          # raza circumscrisa a miezului
    half_width: float      # semi-latimea aripii (v = ±)
    corridor: float        # peretii de coridor la v = ±
    bay: float             # travee pe aripa

    @property
    def apothem(self) -> float:
        return self.radius * math.cos(math.radians(30))

    @property
    def u1(self) -> float:
        """Coordonata u a liniei de la capatul zonei de legatura: acolo aripa are latimea completa si se intalneste cu aripile vecine in crestaturi."""
        return self.half_width / math.tan(math.radians(60))

    def station(self, j: int) -> float:
        """u al liniei transversale j (j = 0: la capatul zonei de legatura)."""
        return self.u1 + j * self.bay

    def glob(self, wing: int, u: float, v: float) -> Pt:
        a = math.radians(120.0 * wing)
        return rnd((u * math.cos(a) - v * math.sin(a), u * math.sin(a) + v * math.cos(a)))

    # ---- miez
    def hex_vertex(self, i: int) -> Pt:
        """Varful i al hexagonului, la unghiul 30° + 60°·i."""
        a = math.radians(30.0 + 60.0 * i)
        return rnd((self.radius * math.cos(a), self.radius * math.sin(a)))

    def face_center(self, i: int) -> Pt:
        a = math.radians(60.0 * i)
        return rnd((self.apothem * math.cos(a), self.apothem * math.sin(a)))

    def face_ends(self, i: int) -> tuple[Pt, Pt]:
        """Varfurile fetei i (normala la 60°·i): varfurile i-1 si i, in sens antiorar."""
        return self.hex_vertex((i - 1) % 6), self.hex_vertex(i % 6)

    def notch(self, w: int) -> Pt:
        """Punctul de crestatura din stanga aripii w (u1, +half_width) = punctul din dreapta aripii w+1."""
        return self.glob(w, self.u1, self.half_width)

    def notch_face(self, w: int) -> int:
        return 2 * w + 1
