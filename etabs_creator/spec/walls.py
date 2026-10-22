"""Peretii structurali: izolati (pe linii de grila), cuplati (grinzi de cuplare) si nuclee in forma de L, C, I, H, T."""
from __future__ import annotations

from dataclasses import dataclass

from ..connect import GenError

CORE_SHAPES = ("", "L", "C", "I", "H", "T")


@dataclass
class WallSpec:
    walls: bool = False
    wall_t: float = 0.25                    # m, grosimea peretilor
    wall_lines_x: str = "first,last"        # liniile de grila (pe Y) pe care sunt pereti paraleli cu X („none” = fara)
    wall_bays_x: str = "middle"             # deschiderile ocupate de acesti pereti
    wall_lines_y: str = "first,last"
    wall_bays_y: str = "middle"
    gravity_frame: bool = True              # stalpi si grinzi in afara peretilor
    belts: bool = True                      # centuri (grinzi „dummy”) deasupra peretilor, la fiecare etaj
    crack_wall_f: float = 0.5               # fisurare pereti: f11, f22, f12 (in plan)
    crack_wall_m: float = 0.25              # m11, m22, m12 (incovoiere din plan)
    coupling_bays_x: str = ""               # grinzi de cuplare in deschiderile dintre doi pereti, pe liniile cu pereti („” = fara)
    coupling_bays_y: str = ""
    coupling_h: float = 0.90                # m, inaltimea grinzii de cuplare (latimea = grosimea peretelui)
    core_shape: str = ""                    # nucleu de pereti: L | C | I | H | T („” = fara)
    core_cells: str = ""                    # „i0,j0,nx,ny” in coordonatele turnului (gol = centrat, ~jumatate din plan)
    walls_through_basement: bool = True     # peretii turnului continua in subsol pana la baza; False = reazema pe placa (DEFECT, pentru a testa verificatorul)

    @property
    def coupled(self) -> bool:
        return bool(self.coupling_bays_x.strip() or self.coupling_bays_y.strip())

    def validate(self) -> None:
        if self.core_shape not in CORE_SHAPES:
            raise GenError("Forma nucleului poate fi L, C, I, H sau T (sau goală).")
        if (self.coupled or self.core_shape) and not self.walls:
            raise GenError("Grinzile de cuplare și nucleele cer pereți (bifează „Cu pereți”).")
        if self.walls:
            if self.wall_t <= 0 or self.coupling_h <= 0:
                raise GenError("Grosimea peretelui și înălțimea grinzii de cuplare trebuie să fie pozitive.")
            for f in ("crack_wall_f", "crack_wall_m"):
                if not 0 < getattr(self, f) <= 1:
                    raise GenError(f"„{f}” trebuie să fie între 0 (exclusiv) și 1.")
