"""Incarcarile pe plansee si coeficientii combinatiilor."""
from __future__ import annotations

from dataclasses import dataclass

from ..connect import GenError


@dataclass
class LoadSpec:
    dead_extra: float = 3.0                 # kN/m2 permanent suplimentar (finisaje + compartimentari)
    live: float = 2.0                       # kN/m2 utila
    gamma_g: float = 1.35                   # ULS, permanent
    gamma_q: float = 1.5                    # ULS, variabil
    psi2: float = 0.3                       # ψ2 al utilei = multiplicatorul ei in sursa de masa

    def validate(self) -> None:
        if self.dead_extra < 0 or self.live < 0:
            raise GenError("Încărcările trebuie să fie nenegative.")
        if self.gamma_g <= 0 or self.gamma_q <= 0 or not 0 <= self.psi2 <= 1:
            raise GenError("γG, γQ trebuie să fie pozitivi și ψ2 între 0 și 1.")
