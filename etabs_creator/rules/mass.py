"""Sursa de masa: masa din elemente + tiparul permanent (x1) + utila (xψ2). Dead nu apare in lista: are deja greutate proprie."""
from __future__ import annotations

from ..tables import upsert_entities


def apply_mass_source(sap, spec, has_perm: bool) -> str:
    pats = ([("Permanenta", "1")] if has_perm else []) + [("Live", f"{spec.psi2:g}")]
    rows = [dict(Name="MsSrc1", IsDefault="Yes", IncLateral="Yes", IncVertical="No", LumpMass="Yes", SourceSelf="Yes", SourceAdded="Yes",
                 SourceLoads="Yes", MoveMass="No", LoadPattern=pats[0][0], Multiplier=pats[0][1])]
    rows += [dict(Name="MsSrc1", LoadPattern=p, Multiplier=m) for p, m in pats[1:]]
    upsert_entities(sap, "Mass Source Definition", "Name", rows)
    return "masă: elemente + " + " + ".join(f"{m}×{p}" for p, m in pats)
