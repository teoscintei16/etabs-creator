"""Nivelurile modelului (de jos in sus), cu subsol: S<n>..S1 (S1 are cota superioara ±0.00), P (parter), E1, E2, ..."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Story:
    name: str
    z_bot: float
    z_top: float
    basement: bool

    @property
    def height(self) -> float:
        return self.z_top - self.z_bot


def stories_of(spec, above: int) -> list[Story]:
    """`above` = numarul de etaje peste teren (cel mai inalt turn). Fara subsol: Story1..StoryN (denumirile implicite ETABS)."""
    out: list[Story] = []
    nb, hb = spec.basement, spec.basement_height
    if nb:
        z = -nb * hb
        for k in range(nb, 0, -1):
            out.append(Story(f"S{k}", z, z + hb, True))
            z += hb
        names = ["P"] + [f"E{i}" for i in range(1, above)]
    else:
        z = 0.0
        names = [f"Story{i}" for i in range(1, above + 1)]
    for i, name in enumerate(names):
        h = spec.bottom if (i == 0 and not nb) else spec.story_height
        out.append(Story(name, z, z + h, False))
        z += h
    return out
