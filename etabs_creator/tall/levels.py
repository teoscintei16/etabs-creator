"""Nivelurile turnului: subsol, niveluri de beton (cu lobby, niveluri tehnice si inaltime tipica calculata) si niveluri de spire."""
from __future__ import annotations

from dataclasses import dataclass

from ..connect import GenError
from ..plan.stories import Story


@dataclass
class TLevel(Story):
    number: int = 0                 # 1.. peste teren (0 la subsol)
    kind: str = "floor"             # basement | floor | mech | spire


def number_list(text: str, what: str) -> list[int]:
    try:
        return sorted({int(t) for t in str(text).replace(";", ",").split(",") if t.strip()})
    except ValueError as e:
        raise GenError(f"„{what}”: numere de niveluri separate prin virgula (ex. 17,40,73).") from e


def level_name(number: int) -> str:
    """Nivelul 1 = P (parter), nivelul n = E{n-1}: la fel ca in restul motorului (ground_story = P)."""
    return "P" if number == 1 else f"E{number - 1}"


def typical_height(spec) -> float:
    mech = [m for m in number_list(spec.mech_levels, "mech_levels") if 2 <= m <= spec.tall_levels]
    count = spec.tall_levels - 1 - len(mech)
    if count < 1:
        raise GenError("Prea multe niveluri tehnice: nu mai rămân niveluri tipice.")
    h = (spec.tall_top_concrete - spec.lobby_height - len(mech) * spec.mech_height) / count
    if h <= 2.5:
        raise GenError(f"Înălțimea tipică rezultată ({h:.2f} m) e prea mică: crește cota vârfului betonului sau scade numărul de niveluri.")
    return h


def build_levels(spec) -> list[TLevel]:
    out: list[TLevel] = []
    nb, hb = spec.basement, spec.basement_height
    z = -nb * hb
    for k in range(nb, 0, -1):
        out.append(TLevel(f"S{k}", z, z + hb, True, 0, "basement"))
        z += hb
    mech = set(number_list(spec.mech_levels, "mech_levels"))
    typ = typical_height(spec)
    zx = z
    for n in range(1, spec.tall_levels + 1):
        kind = "mech" if n in mech and n >= 2 else "floor"
        h = spec.lobby_height if n == 1 else (spec.mech_height if kind == "mech" else typ)
        zx += h                                                 # cota exacta (fara deriva); cotele din model sunt pe grila de 1 mm („noduri cu zecimale parazite”)
        top = round(zx, 3)
        out.append(TLevel(level_name(n), z, top, False, n, kind))
        z = top
    hs = (spec.tall_top - z) / spec.tall_spire_levels
    last = spec.tall_levels + spec.tall_spire_levels
    for n in range(spec.tall_levels + 1, last + 1):
        zx += hs
        top = spec.tall_top if n == last else round(zx, 3)
        out.append(TLevel(level_name(n), z, top, False, n, "spire"))
        z = top
    return out
