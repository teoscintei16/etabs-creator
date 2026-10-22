"""Actiunea seismica P100-1 (calcule pure): spectrul de proiectare Sd(T) si coeficientul seismic al fortelor statice."""
from __future__ import annotations

from dataclasses import dataclass

G = 9.81
BETA_LIM = 0.2                      # Sd(T) >= 0.2·ag·γI (P100-1)


@dataclass
class SeismicParams:
    ag: float = 0.20                # acceleratia de proiectare, in multipli de g
    gamma_I: float = 1.0
    beta0: float = 2.5
    Tb: float = 0.07
    Tc: float = 0.7
    Td: float = 3.0
    q: float = 3.5
    lam: float = 0.85               # λ, factorul de corectie al fortei taietoare de baza
    ecc: float = 0.05               # excentricitatea accidentala (fractiune din latura)
    damping: float = 0.05
    psi2: float = 0.3               # coeficientul cvasi-permanent al incarcarii utile (si multiplicatorul de masa)
    orth: float = 0.3               # componenta ortogonala


def params_from(spec) -> SeismicParams:
    """SeismicParams din ModelSpec (seism + ψ2 din incarcari)."""
    return SeismicParams(ag=spec.ag, gamma_I=spec.gamma_I, beta0=spec.beta0, Tb=spec.Tb, Tc=spec.Tc, Td=spec.Td, q=spec.q, lam=spec.lam,
                         ecc=spec.ecc, damping=spec.damping, psi2=spec.psi2, orth=spec.orth)


def shape(T: float, p: SeismicParams) -> float:
    """Sd(T)/(ag·γI·g) pentru factorul de comportare q."""
    b = p.beta0 / p.q
    if T <= p.Tb:
        return 1.0 + (b - 1.0) * T / p.Tb if p.Tb > 0 else b
    if T <= p.Tc:
        return b
    if T <= p.Td:
        return b * p.Tc / T
    return b * p.Tc * p.Td / T ** 2


def sd(T: float, p: SeismicParams) -> float:
    """Spectrul de proiectare Sd(T) in m/s² (γI inclus, cu minimul 0.2)."""
    return p.ag * G * p.gamma_I * max(shape(T, p), BETA_LIM)


def spectrum_points(p: SeismicParams) -> list[tuple[float, float]]:
    """Punctele functiei spectrale user-defined: (T [s], Sd [m/s²]). Include colturile TB, TC, TD si coada pana la 6 s."""
    ts = sorted({0.0, p.Tb, p.Tc, p.Td, *[round(0.1 * k, 2) for k in range(2, 10)], 1.0, 1.25, 1.5, 2.0, 2.5, 3.5, 4.0, 5.0, 6.0})
    return [(t, round(sd(t, p), 5)) for t in ts]


def seismic_coefficient(p: SeismicParams) -> float:
    """Coeficientul seismic C al fortelor statice echivalente pe platou: λ·γI·ag·β0/q."""
    return round(p.lam * p.gamma_I * p.ag * p.beta0 / p.q, 5)


def coefficient_for_period(T: float, p: SeismicParams) -> float:
    """C = λ·Sd(T1)/g: coeficientul fortelor statice pentru perioada fundamentala T1 (cum il calculeaza si verificatorul)."""
    return round(p.lam * sd(T, p) / G, 5)
