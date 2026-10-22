"""Subsolul: niveluri sub ±0.00 pe planul complet al grilei, pereti perimetrali si impingerea pamantului."""
from __future__ import annotations

from dataclasses import dataclass

from ..connect import GenError


@dataclass
class BasementSpec:
    basement: int = 0                       # numar de niveluri de subsol (0 = fara)
    basement_height: float = 3.0
    basement_wall_t: float = 0.30
    soil_pressure: float = 25.0             # kN/m2, impingerea pamantului (uniforma, simplificata)

    def validate(self) -> None:
        if not 0 <= self.basement <= 4:
            raise GenError("Numărul de niveluri de subsol trebuie să fie între 0 și 4.")
        if self.basement and (self.basement_height <= 0 or self.basement_wall_t <= 0 or self.soil_pressure < 0):
            raise GenError("Înălțimea subsolului și grosimea pereților de subsol trebuie să fie pozitive, iar presiunea pământului nenegativă.")
