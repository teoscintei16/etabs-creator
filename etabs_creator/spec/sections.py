"""Materialul si sectiunile elementelor de cadru si plansee."""
from __future__ import annotations

from dataclasses import dataclass

from ..connect import GenError

# clasa betonului -> (fck [kN/m2], Ecm [kN/m2]) conform EN 1992-1-1
CONCRETE = {"C20/25": (20e3, 30e6), "C25/30": (25e3, 31e6), "C30/37": (30e3, 33e6), "C35/45": (35e3, 34e6), "C40/50": (40e3, 35e6),
            "C50/60": (50e3, 37e6), "C60/75": (60e3, 39e6), "C70/85": (70e3, 41e6), "C80/95": (80e3, 42e6)}


@dataclass
class SectionSpec:
    column_b: float = 0.50                  # m, latimea stalpului
    column_h: float = 0.50                  # m, inaltimea sectiunii stalpului
    beam_b: float = 0.30
    beam_h: float = 0.60
    slab_t: float = 0.15
    concrete: str = "C25/30"
    diaphragm: str = "semirigid"            # semirigid | rigid

    def validate(self) -> None:
        for f in ("column_b", "column_h", "beam_b", "beam_h", "slab_t"):
            if getattr(self, f) <= 0:
                raise GenError(f"Valoarea „{f}” trebuie să fie pozitivă.")
        if self.concrete not in CONCRETE:
            raise GenError(f"Clasă de beton necunoscută: {self.concrete}")
        if self.diaphragm not in ("semirigid", "rigid"):
            raise GenError("Diafragma poate fi „semirigid” sau „rigid”.")
