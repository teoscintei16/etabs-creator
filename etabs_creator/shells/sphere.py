"""Coaja ca petic de sfera (ca la Opera din Sydney: toate coastele sunt arce de cerc mare ale aceleiasi sfere, de raza R).

Triunghiul sferic e dat de trei varfuri: A (varful evantaiului de coaste, la piedestal), B (celalalt capat al bazei, pe podium) si C (creasta).
Muchia AB e coasta de baza; coastele se desfasoara din A spre muchia frontala BC; AC e muchia laterala care urca la creasta."""
from __future__ import annotations

import math

from ..connect import GenError
from .vec import V3, add, cross, dot, mul, norm, sub, unit


def sphere_center(a: V3, b: V3, c: V3, radius: float) -> V3:
    """Centrul sferei de raza `radius` care trece prin A, B, C; din cele doua solutii se alege cea de jos (coaja convexa spre cer)."""
    ab, ac = sub(b, a), sub(c, a)
    n = cross(ab, ac)
    n2 = dot(n, n)
    if n2 < 1e-9:
        raise GenError("Varfurile cojii sunt coliniare.")
    # centrul cercului circumscris triunghiului
    to_m = add(mul(cross(n, ab), dot(ac, ac) / (2 * n2)), mul(cross(ac, n), dot(ab, ab) / (2 * n2)))
    m = add(a, to_m)
    r = norm(to_m)
    if r >= radius:
        raise GenError(f"Coaja nu încape pe sfera de rază {radius:g} m (cercul circumscris are rază {r:.1f} m): micșorează baza sau înălțimea.")
    h = math.sqrt(radius * radius - r * r)
    nu = unit(n)
    lower = add(m, mul(nu, -h)) if nu[2] > 0 else add(m, mul(nu, h))
    return lower


def point_on(center: V3, radius: float, a: V3, b: V3, c: V3, s: float, t: float) -> V3:
    """Punctul (s, t) al petecului: s = 0 in A, s = 1 pe muchia BC; t = 0 pe muchia AB, t = 1 pe AC."""
    da, db, dc = unit(sub(a, center)), unit(sub(b, center)), unit(sub(c, center))
    far = add(mul(db, 1 - t), mul(dc, t))
    d = unit(add(mul(da, 1 - s), mul(far, s)))
    return add(center, mul(d, radius))


def s_for_base_y(center: V3, radius: float, a: V3, b: V3, c: V3, y: float) -> float:
    """Parametrul s al punctului de pe coasta de baza (t = 0) cu coordonata y data (bisectie; y creste monoton de la A la B)."""
    lo, hi = 0.0, 1.0
    up = b[1] >= a[1]
    for _ in range(60):
        mid = (lo + hi) / 2
        py = point_on(center, radius, a, b, c, mid, 0.0)[1]
        if (py < y) == up:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2
