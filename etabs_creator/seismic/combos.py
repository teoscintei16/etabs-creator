"""Lista combinatiilor de incarcari (pura): ULS, SLS caracteristica si cvasi-permanenta, seismice (± si cu componenta ortogonala)."""
from __future__ import annotations

from .spectrum import SeismicParams

Combo = tuple[str, list[tuple[str, float]]]


def gravity_combos(has_perm: bool, p: SeismicParams, gamma_g: float, gamma_q: float, extra_perm: list[str]) -> list[Combo]:
    """ULS, SLS_CAR, SLS_QP. `extra_perm` = tipare permanente suplimentare (ex. impingerea pamantului), doar aici, nu in cele seismice."""
    perm = [("Permanenta", 1.0)] if has_perm else []
    permu = [("Permanenta", gamma_g)] if has_perm else []
    return [("ULS", [("Dead", gamma_g), *permu, ("Live", gamma_q), *[(e, gamma_g) for e in extra_perm]]),
            ("SLS_CAR", [("Dead", 1.0), *perm, ("Live", 1.0), *[(e, 1.0) for e in extra_perm]]),
            ("SLS_QP", [("Dead", 1.0), *perm, ("Live", p.psi2), *[(e, 1.0) for e in extra_perm]])]


def wind_combos(has_perm: bool, wind: list[str], p: SeismicParams, gamma_g: float, gamma_q: float) -> list[Combo]:
    """Vant: ULS cu permanent defavorabil si cu permanent favorabil (ridicare), SLS caracteristica. Utila cu ψ0 = 0,7."""
    perm = [("Permanenta", 1.0)] if has_perm else []
    permu = [("Permanenta", gamma_g)] if has_perm else []
    out: list[Combo] = []
    for w in wind:
        for sign, tag in ((1.0, ""), (-1.0, "_neg")):
            out += [(f"ULS_{w}{tag}", [("Dead", gamma_g), *permu, ("Live", 0.7 * gamma_q), (w, sign * gamma_q)]),
                    (f"ULS_{w}_fav{tag}", [("Dead", 1.0), *perm, (w, sign * gamma_q)]),
                    (f"SLS_{w}{tag}", [("Dead", 1.0), *perm, ("Live", 0.7), (w, sign)])]
    return out


def seismic_combos(has_perm: bool, static: list[str], rs: list[str], p: SeismicParams) -> list[Combo]:
    """G + ψ2·Q ± E: pure (±) si cu componenta ortogonala ±orth·E. Partea gravitationala = multiplicatorii sursei de masa."""
    perm = [("Permanenta", 1.0)] if has_perm else []
    grav = [("Dead", 1.0), *perm, ("Live", p.psi2)]
    axis = {n: ("X" if n[1] == "X" else "Y") for n in static}
    out: list[Combo] = []
    for a in static:
        for sa in (1, -1):
            out.append((f"S_{'+' if sa > 0 else '-'}{a}", grav + [(a, float(sa))]))
            for b in static:
                if axis[b] == axis[a]:
                    continue
                for sb in (1, -1):
                    out.append((f"S_{'+' if sa > 0 else '-'}{a}_{'+' if sb > 0 else '-'}{p.orth:g}{b}", grav + [(a, float(sa)), (b, sb * p.orth)]))
    for r in rs:
        for s in (1, -1):
            out.append((f"S_{'+' if s > 0 else '-'}{r}", grav + [(r, float(s))]))
    return out


def combos(has_perm: bool, static: list[str], rs: list[str], p: SeismicParams, gamma_g: float = 1.35, gamma_q: float = 1.5,
           extra_perm: list[str] | tuple[str, ...] = (), wind: list[str] | tuple[str, ...] = ()) -> list[Combo]:
    return (gravity_combos(has_perm, p, gamma_g, gamma_q, list(extra_perm)) + wind_combos(has_perm, list(wind), p, gamma_g, gamma_q)
            + seismic_combos(has_perm, static, rs, p))
