"""Operatii minime pe vectori 3D (tuple), fara dependente."""
from __future__ import annotations

import math

V3 = tuple[float, float, float]


def add(a: V3, b: V3) -> V3:
    return a[0] + b[0], a[1] + b[1], a[2] + b[2]


def sub(a: V3, b: V3) -> V3:
    return a[0] - b[0], a[1] - b[1], a[2] - b[2]


def mul(a: V3, k: float) -> V3:
    return a[0] * k, a[1] * k, a[2] * k


def dot(a: V3, b: V3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: V3, b: V3) -> V3:
    return a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]


def norm(a: V3) -> float:
    return math.sqrt(dot(a, a))


def unit(a: V3) -> V3:
    n = norm(a)
    return a[0] / n, a[1] / n, a[2] / n
