"""Defecte intentionate, pentru a testa verificatorul si reparatiile lui. Se cer prin `defects` (nume separate prin virgula) si se aplica dupa reguli."""
from __future__ import annotations

from ..connect import GenError
from . import analysis_defects, element_defects, load_defects, mesh_defects  # noqa: F401  (inregistreaza defectele)
from .registry import DEFECTS, DESCRIPTIONS


def parse(text: str) -> list[str]:
    names = [t.strip() for t in str(text).split(",") if t.strip()]
    unknown = [n for n in names if n not in DEFECTS]
    if unknown:
        raise GenError(f"Defecte necunoscute: {', '.join(unknown)} (disponibile: {', '.join(DEFECTS)}).")
    return names


def apply_defects(c) -> list[str]:
    """Aplica defectele cerute in spec; intoarce notele."""
    return [f"DEFECT {n}: {DEFECTS[n](c)}" for n in parse(c.spec.defects)]


__all__ = ["DEFECTS", "DESCRIPTIONS", "apply_defects", "parse"]
