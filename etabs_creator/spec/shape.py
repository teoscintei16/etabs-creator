"""Forma in plan a fiecarui turn: dreptunghi, L, retragere pe inaltime, goluri in plansee."""
from __future__ import annotations

from dataclasses import dataclass

from ..connect import GenError


@dataclass
class ShapeSpec:
    shape: str = "rect"                     # rect | L | setback
    cut_bays: int = 1                       # L: deschideri taiate din coltul (x, y) maxim al turnului
    cut_travei: int = 1
    setback_story: int = 3                  # setback: planul se reduce deasupra acestui etaj
    setback_bays: int = 1                   # deschideri eliminate pe latura x maxima
    void_cells: str = ""                    # goluri in plansee: celule „i,j;i,j” in coordonatele turnului

    def validate(self) -> None:
        if self.shape not in ("rect", "L", "setback"):
            raise GenError("Forma poate fi „rect”, „L” sau „setback”.")
