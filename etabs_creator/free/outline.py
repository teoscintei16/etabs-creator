"""Conturul in plan al unei structuri cu plan liber: lista de puncte (x, y), in sens trigonometric, centrata pe centroid (origine).

Conturul trebuie sa fie stelat fata de centroid (fiecare latura vazuta din centru in sens trigonometric): retea radiala de inele."""
from __future__ import annotations

import math

from ..connect import GenError
from .spline import Pt, catmull_rom_closed, parse_points


def _circle(r: float, ry: float, m: int) -> list[Pt]:
    return [(r * math.cos(2 * math.pi * j / m), ry * math.sin(2 * math.pi * j / m)) for j in range(m)]


def _semicircle(r: float, m: int) -> list[Pt]:
    """Arc de la 0 la π, apoi diametrul inapoi (punctele de pe diametru se adauga la subdivizare)."""
    k = max(6, int(m * 0.6))
    arc = [(r * math.cos(math.pi * j / k), r * math.sin(math.pi * j / k)) for j in range(k + 1)]       # (R, 0) ... (-R, 0)
    return arc                                                                                       # (-R, 0) -> (R, 0) e latura inchisa


def _polygon(r: float, n: int) -> list[Pt]:
    return [(r * math.cos(2 * math.pi * j / n + math.pi / n), r * math.sin(2 * math.pi * j / n + math.pi / n)) for j in range(n)]


def _trapezoid(b: float, t: float, d: float) -> list[Pt]:
    return [(-b / 2, -d / 2), (b / 2, -d / 2), (t / 2, d / 2), (-t / 2, d / 2)]


def _lobed(r: float, k: int, amp: float, m: int) -> list[Pt]:
    return [((r * (1 + amp * math.cos(k * th))) * math.cos(th), (r * (1 + amp * math.cos(k * th))) * math.sin(th))
            for th in (2 * math.pi * j / m for j in range(m))]


def signed_area(pts: list[Pt]) -> float:
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))


def centroid(pts: list[Pt]) -> Pt:
    a = signed_area(pts)
    if abs(a) < 1e-9:
        raise GenError("Conturul are arie nulă.")
    cx = sum((p[0] + q[0]) * (p[0] * q[1] - q[0] * p[1]) for p, q in zip(pts, pts[1:] + pts[:1])) / (6 * a)
    cy = sum((p[1] + q[1]) * (p[0] * q[1] - q[0] * p[1]) for p, q in zip(pts, pts[1:] + pts[:1])) / (6 * a)
    return cx, cy


def subdivide(pts: list[Pt], max_len: float) -> list[Pt]:
    """Imparte laturile mai lungi de `max_len` in parti egale (conturul ramane inchis, fara a repeta primul punct)."""
    out: list[Pt] = []
    for a, b in zip(pts, pts[1:] + pts[:1]):
        k = max(1, math.ceil(math.dist(a, b) / max_len))
        out += [(a[0] + (b[0] - a[0]) * t / k, a[1] + (b[1] - a[1]) * t / k) for t in range(k)]
    return out


def is_star_shaped(pts: list[Pt]) -> bool:
    """Fiecare latura, vazuta din origine, parcurge unghiul in sens trigonometric (produs vectorial pozitiv)."""
    return all(a[0] * b[1] - a[1] * b[0] > 1e-9 for a, b in zip(pts, pts[1:] + pts[:1]))


def outline(spec) -> list[Pt]:
    """Conturul formei alese, subdivizat, trigonometric, centrat pe centroid; GenError daca nu e stelat fata de centroid."""
    s = spec.free_shape
    if s == "circle":
        pts = _circle(spec.free_radius, spec.free_radius, spec.free_samples)
    elif s == "ellipse":
        pts = _circle(spec.free_radius, spec.free_radius_y, spec.free_samples)
    elif s == "semicircle":
        pts = _semicircle(spec.free_radius, spec.free_samples)
    elif s == "polygon":
        pts = _polygon(spec.free_radius, spec.free_sides)
    elif s == "trapezoid":
        pts = _trapezoid(spec.trap_bottom, spec.trap_top, spec.trap_depth)
    elif s == "lobed":
        pts = _lobed(spec.free_radius, spec.lobes, spec.lobe_amp, spec.free_samples)
    elif s == "spline":
        pts = catmull_rom_closed(parse_points(spec.spline_points))
    else:
        raise GenError(f"Formă liberă necunoscută: {s}")
    if signed_area(pts) < 0:
        pts = pts[::-1]
    cx, cy = centroid(pts)
    pts = [(x - cx, y - cy) for x, y in pts]
    pts = subdivide(pts, spec.free_edge_max)
    if not is_star_shaped(pts):
        raise GenError("Conturul nu e stelat față de centroid (o latură „se întoarce” văzută din centru): simplifică forma sau mărește retragerile.")
    return pts
