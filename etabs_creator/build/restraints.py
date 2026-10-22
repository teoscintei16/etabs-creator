"""Rezemarea la baza: toate nodurile de la cota bazei (capete de stalpi si colturile peretilor) incastrate."""
from __future__ import annotations

from ..connect import ok
from .context import Ctx


def restrain_base(c: Ctx) -> int:
    pts = list(dict.fromkeys(c.base_points))
    for p in pts:
        ok(c.sap.PointObj.SetRestraint(p, [True] * 6), "SetRestraint")
    return len(pts)
