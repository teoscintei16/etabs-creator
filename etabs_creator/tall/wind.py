"""Vantul pe inaltime: forta pe nivel = q(z) · Cf · B(z) · h, cu profilul q(z) = q10 · (z/10)^(2α)."""
from __future__ import annotations


def pressure(z: float, q10: float, alpha: float) -> float:
    return q10 * (max(z, 10.0) / 10.0) ** (2.0 * alpha)


def story_force(z_mid: float, height: float, width: float, q10: float, alpha: float, cf: float) -> float:
    """kN: presiunea la mijlocul nivelului × coeficient de forta × latimea proiectata × inaltimea nivelului."""
    return pressure(z_mid, q10, alpha) * cf * width * height
