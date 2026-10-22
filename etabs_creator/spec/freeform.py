"""Structuri cu plan liber: cerc, elipsa, semicerc, poligon, trapez, forma cu lobi, spline; piramide (reducere pe inaltime), rasucire, inclinare."""
from __future__ import annotations

from dataclasses import dataclass

from ..connect import GenError

SHAPES = ("", "circle", "ellipse", "semicircle", "polygon", "trapezoid", "lobed", "spline")
COLUMN_MODES = ("perimeter", "all", "none")


@dataclass
class FreeformSpec:
    free_shape: str = ""                    # „” = grila ortogonala; altfel una din SHAPES
    free_radius: float = 12.0               # m: cerc, semicerc, poligon (raza cercului circumscris), lobi (raza de baza), elipsa (semiaxa pe X)
    free_radius_y: float = 8.0              # m: semiaxa pe Y a elipsei
    free_sides: int = 6                     # poligon regulat
    trap_bottom: float = 24.0               # m: trapez, latura de jos (pe X)
    trap_top: float = 12.0                  # latura de sus
    trap_depth: float = 14.0                # adancimea pe Y
    lobes: int = 5                          # forma cu lobi: r = R·(1 + amp·cos(lobi·θ))
    lobe_amp: float = 0.25
    spline_points: str = "12,0;8,9;0,13;-9,9;-13,0;-8,-8;0,-12;9,-9"   # puncte de control „x,y;x,y”, spline inchis (Catmull-Rom)
    free_samples: int = 24                  # puncte pe contur pentru formele curbe
    free_edge_max: float = 5.0              # m: laturile drepte mai lungi se impart
    free_rings: int = 3                     # inele de la centru la contur (retea radiala de grinzi si placi)
    atrium: float = 0.0                     # 0..0.8: raza golului central, fractiune din contur
    free_columns: str = "all"               # all | perimeter | none
    free_wall_edges: str = "none"           # pereti pe laturile conturului: none | all | alternate | indici „0,3,6”
    taper: float = 0.0                      # 0..0.9: reducerea planului la ultimul nivel (piramida): scara = 1 − taper·nivel/etaje
    step_every: int = 0                     # piramida in trepte: la fiecare atatea etaje planul se reduce (0 = fara)
    step_scale: float = 0.85                # factorul de reducere la fiecare treapta
    twist_deg: float = 0.0                  # rasucire pe etaj (grade): fara pereti
    lean_x: float = 0.0                     # inclinare pe etaj (m)
    lean_y: float = 0.0

    @property
    def free_walls_on(self) -> bool:
        return bool(self.free_shape) and self.free_wall_edges.strip().lower() not in ("", "none")

    def validate(self) -> None:
        if self.free_shape not in SHAPES:
            raise GenError(f"Formă liberă necunoscută: {self.free_shape} (alege din {', '.join(s for s in SHAPES if s)}).")
        if not self.free_shape:
            return
        for f in ("free_radius", "free_radius_y", "trap_bottom", "trap_top", "trap_depth", "free_edge_max"):
            if getattr(self, f) <= 0:
                raise GenError(f"„{f}” trebuie să fie pozitiv.")
        if not 3 <= self.free_sides <= 64 or not 8 <= self.free_samples <= 200 or not 1 <= self.free_rings <= 12 or not 2 <= self.lobes <= 24:
            raise GenError("Laturi 3–64, puncte pe contur 8–200, inele 1–12, lobi 2–24.")
        if not 0 <= self.atrium <= 0.8 or not 0 <= self.taper <= 0.9 or not 0 < self.step_scale <= 1 or not 0 <= self.lobe_amp < 1:
            raise GenError("Atriu 0–0,8; reducere 0–0,9; factor de treaptă (0, 1]; amplitudinea lobilor 0–1.")
        if self.step_every < 0 or self.free_columns not in COLUMN_MODES:
            raise GenError("Treapta trebuie să fie ≥ 0; coloanele: perimeter, all sau none.")
        if self.free_walls_on and abs(self.twist_deg) > 1e-9:
            raise GenError("Pereții nu se pot desena la o structură răsucită (panouri neplane): pune rasucirea pe 0 sau scoate pereții.")
        if self.free_walls_on and self.step_every:
            pass                            # treptele au pereti verticali pe fiecare etaj (se vor semnala la continuitate, ca la o structura reala in trepte)
