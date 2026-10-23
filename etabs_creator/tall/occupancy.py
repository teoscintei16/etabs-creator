"""Ocuparea pe niveluri si seturile de incarcari uniforme (Shell Uniform Load Sets): nume -> (permanent, utila) kN/m2."""
from __future__ import annotations

from ..connect import GenError
from .levels import TLevel


def parse_sets(text: str) -> dict[str, tuple[float, float]]:
    out: dict[str, tuple[float, float]] = {}
    for tok in (t.strip() for t in text.split(";") if t.strip()):
        try:
            name, perm, live = tok.split(":")
            out[name.strip()] = (float(perm), float(live))
        except ValueError as e:
            raise GenError(f"Set de încărcări „{tok}”: formatul e nume:permanent:utila (ex. MALL:2.5:5.0).") from e
    return out


def parse_occupancy(text: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for tok in (t.strip() for t in text.split(";") if t.strip()):
        try:
            rng, name = tok.split(":")
            a, _, b = rng.partition("-")
            for n in range(int(a), int(b or a) + 1):
                out[n] = name.strip()
        except ValueError as e:
            raise GenError(f"Ocupare „{tok}”: formatul e de-la-pana:SET (ex. 4-16:HOTEL).") from e
    return out


def set_of(level: TLevel, occupancy: dict[int, str]) -> str:
    """Setul de incarcari al planseului nivelului: subsol = PARCARE, nivel tehnic = TEHNIC, altfel dupa tabelul de ocupare."""
    if level.kind == "basement":
        return "PARCARE"
    if level.kind == "mech":
        return "TEHNIC"
    if level.number not in occupancy:
        raise GenError(f"Nivelul {level.number} nu are ocupare (completeaza „occupancy”).")
    return occupancy[level.number]


def check_sets(spec, levels: list[TLevel]) -> dict[str, tuple[float, float]]:
    """Seturile definite; ridica GenError daca un nivel foloseste un set nedefinit."""
    sets = parse_sets(spec.load_sets)
    occ = parse_occupancy(spec.occupancy)
    for lv in levels:
        if lv.kind == "spire":
            continue
        name = set_of(lv, occ)
        if name not in sets:
            raise GenError(f"Nivelul {lv.name} folosește setul „{name}”, nedefinit în „load_sets”.")
    return sets
