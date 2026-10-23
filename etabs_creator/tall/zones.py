"""Zonele de sectiuni pe inaltime: beton, grosimea peretilor, stalpii, placa."""
from __future__ import annotations

from dataclasses import dataclass

from ..connect import GenError
from ..spec.sections import CONCRETE


@dataclass(frozen=True)
class Zone:
    first: int
    last: int
    grade: str
    wall_t: float
    col: float
    slab_t: float

    @property
    def key(self) -> str:
        return f"{self.first}-{self.last}"


def parse_zones(spec) -> list[Zone]:
    out: list[Zone] = []
    for tok in (t.strip() for t in spec.zones.split(";") if t.strip()):
        try:
            rng, grade, wall, col, slab = tok.split(":")
            a, b = (int(x) for x in rng.split("-"))
            z = Zone(a, b, grade, float(wall), float(col), float(slab))
        except ValueError as e:
            raise GenError(f"Zona „{tok}”: formatul e de-la-pana:beton:perete:stalp:placa (ex. 1-40:C80/95:1.3:1.4:0.3).") from e
        if z.grade not in CONCRETE:
            raise GenError(f"Zona „{tok}”: clasă de beton necunoscută ({z.grade}).")
        if z.first > z.last or min(z.wall_t, z.col, z.slab_t) <= 0:
            raise GenError(f"Zona „{tok}”: interval sau dimensiuni invalide.")
        out.append(z)
    out.sort(key=lambda z: z.first)
    covered = [n for z in out for n in range(z.first, z.last + 1)]
    if covered != list(range(1, spec.tall_levels + 1)):
        raise GenError(f"Zonele trebuie să acopere exact nivelurile 1…{spec.tall_levels}, fără suprapuneri sau goluri.")
    return out


def zone_of(zones: list[Zone], number: int) -> Zone:
    return next(z for z in zones if z.first <= number <= z.last)
