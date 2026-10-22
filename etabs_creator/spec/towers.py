"""Turnurile peste teren: dreptunghiuri de celule din grila totala, fiecare cu numarul lui de etaje."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TowerSpec:
    towers: str = ""                        # „i0,j0,nx,ny,etaje;…” (gol = un singur turn pe toata grila, cu `stories` etaje)

    def validate(self) -> None:
        pass                                # validarea cere grila: vezi plan.towers.towers_of
