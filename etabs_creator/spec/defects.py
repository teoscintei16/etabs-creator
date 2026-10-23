"""Defecte intentionate (pentru testarea verificatorului si a reparatiilor lui)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DefectSpec:
    defects: str = ""                       # nume separate prin virgula; vezi etabs_creator.defects.DEFECTS

    def validate(self) -> None:
        if self.defects.strip():
            from ..defects import parse
            parse(self.defects)
