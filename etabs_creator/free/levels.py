"""Transformarea planului pe nivele: scara (piramida neteda sau in trepte), rasucire si inclinare. Calcule pure."""
from __future__ import annotations

import math
from dataclasses import dataclass

Pt = tuple[float, float]


@dataclass(frozen=True)
class Level:
    scale: float = 1.0
    angle: float = 0.0          # radiani
    dx: float = 0.0
    dy: float = 0.0

    def apply(self, p: Pt) -> Pt:
        c, s = math.cos(self.angle), math.sin(self.angle)
        x, y = p[0] * self.scale, p[1] * self.scale
        return x * c - y * s + self.dx, x * s + y * c + self.dy


def smooth_level(spec, k: int, n: int) -> Level:
    """Nivelul k (0..n, k = 0 la cota ±0.00 / baza turnului): scara 1 − taper·k/n, rasucire si inclinare liniare."""
    return Level(1.0 - spec.taper * k / max(n, 1), math.radians(spec.twist_deg) * k, spec.lean_x * k, spec.lean_y * k)


def step_level(spec, story: int) -> Level:
    """Treapta in care se afla etajul `story` (1..n): scara scade cu `step_scale` la fiecare `step_every` etaje."""
    steps = (story - 1) // spec.step_every if spec.step_every else 0
    return Level(spec.step_scale ** steps, 0.0, spec.lean_x * story, spec.lean_y * story)


def story_levels(spec, story: int, n: int) -> tuple[Level, Level]:
    """(nivelul de jos, nivelul de sus) al etajului `story` (1..n). In trepte, etajul are aceeasi scara jos si sus (elemente verticale)."""
    if spec.step_every:
        lv = step_level(spec, story)
        return lv, lv
    return smooth_level(spec, story - 1, n), smooth_level(spec, story, n)
