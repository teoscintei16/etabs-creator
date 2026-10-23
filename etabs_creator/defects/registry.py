"""Registrul defectelor intentionate: fiecare stricheaza modelul intr-un fel pe care verificatorul trebuie sa-l semnaleze (si, unde exista, sa-l repare)."""
from __future__ import annotations

from typing import Callable

DEFECTS: dict[str, Callable] = {}
DESCRIPTIONS: dict[str, str] = {}


def defect(name: str, description: str):
    """Inregistreaza `fn(ctx) -> str` (nota despre ce s-a stricat)."""
    def deco(fn):
        DEFECTS[name] = fn
        DESCRIPTIONS[name] = description
        return fn
    return deco
