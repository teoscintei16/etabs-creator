"""Grila si inaltimile: etaje (peste teren), deschideri pe X, travei pe Y."""
from __future__ import annotations

from dataclasses import dataclass

from ..connect import GenError


@dataclass
class GridSpec:
    stories: int = 5                        # x: numar de etaje peste teren (la cel mai inalt turn)
    bays: int = 3                           # y: deschideri pe directia X (planul total, inclusiv subsolul)
    travei: int = 3                         # z: travei pe directia Y
    story_height: float = 3.0               # m
    bottom_height: float | None = None      # m, primul etaj fara subsol (implicit = story_height)
    span_x: float = 5.0                     # m
    span_y: float = 5.0                     # m

    def validate(self) -> None:
        if not 1 <= self.stories <= 60:
            raise GenError("Numărul de etaje trebuie să fie între 1 și 60.")
        if not (1 <= self.bays <= 30 and 1 <= self.travei <= 30):
            raise GenError("Deschiderile și traveile trebuie să fie între 1 și 30.")
        for f in ("story_height", "span_x", "span_y"):
            if getattr(self, f) <= 0:
                raise GenError(f"Valoarea „{f}” trebuie să fie pozitivă.")
        if self.bottom_height is not None and self.bottom_height <= 0:
            raise GenError("Înălțimea primului etaj trebuie să fie pozitivă.")

    @property
    def bottom(self) -> float:
        return self.story_height if self.bottom_height is None else self.bottom_height
