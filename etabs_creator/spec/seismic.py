"""Parametrii actiunii seismice P100-1 (completati de utilizator; valorile implicite sunt orientative, fara oras)."""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..connect import GenError


@dataclass
class SeismicSpec:
    seismic: bool = True                    # False = fara actiune seismica (doar gravitational)
    ag: float = 0.20                        # in multipli de g
    gamma_I: float = 1.0
    beta0: float = 2.5
    Tb: float = 0.07
    Tc: float = 0.7
    Td: float = 3.0
    q: float = 3.5
    lam: float = 0.85
    ecc: float = 0.05
    damping: float = 0.05
    orth: float = 0.3
    calibrate_static: bool = True           # dupa o analiza modala, C al fortelor statice se ia pentru T1 pe fiecare directie

    def validate(self) -> None:
        if not self.seismic:
            return
        for f in ("ag", "gamma_I", "beta0", "Tb", "Tc", "Td", "q", "lam"):
            v = getattr(self, f)
            if not (isinstance(v, (int, float)) and math.isfinite(v) and v > 0):
                raise GenError(f"Parametrul seismic „{f}” trebuie să fie pozitiv.")
        if not self.Tb < self.Tc < self.Td:
            raise GenError("Trebuie TB < TC < TD.")
