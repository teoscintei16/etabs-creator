"""Spline inchis Catmull-Rom prin puncte de control (curba trece prin puncte)."""
from __future__ import annotations

from ..connect import GenError

Pt = tuple[float, float]


def parse_points(text: str) -> list[Pt]:
    """„x,y;x,y;…” -> lista de puncte (cel putin 4)."""
    pts: list[Pt] = []
    for tok in (t.strip() for t in str(text).split(";") if t.strip()):
        try:
            x, y = (float(v) for v in tok.split(","))
        except ValueError as e:
            raise GenError(f"Punct de control „{tok}”: folosește formatul x,y (ex. 12,0;8,9;0,13).") from e
        pts.append((x, y))
    if len(pts) < 4:
        raise GenError("Spline-ul cere cel puțin 4 puncte de control.")
    return pts


def catmull_rom_closed(ctrl: list[Pt], per_segment: int = 8) -> list[Pt]:
    """Puncte pe spline-ul inchis (parametrizare uniforma, tensiune 0.5): `per_segment` puncte intre doua puncte de control, fara a repeta primul."""
    n = len(ctrl)
    out: list[Pt] = []
    for i in range(n):
        p0, p1, p2, p3 = ctrl[(i - 1) % n], ctrl[i], ctrl[(i + 1) % n], ctrl[(i + 2) % n]
        for k in range(per_segment):
            t = k / per_segment
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3)
                             for a, b, c, d in zip(p0, p1, p2, p3)))
    return out
