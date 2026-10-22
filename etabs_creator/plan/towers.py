"""Turnurile: dreptunghiuri de celule ale grilei totale, fiecare cu etajele lui. Fara specificatie = un singur turn pe toata grila."""
from __future__ import annotations

from dataclasses import dataclass

from ..connect import GenError


@dataclass
class Tower:
    index: int                              # 1, 2, ...
    i0: int
    j0: int
    nx: int
    ny: int
    stories: int
    prefix: str = ""                        # „T2_” cand exista mai multe turnuri (pentru etichete Pier / Spandrel)

    @property
    def cells(self) -> set[tuple[int, int]]:
        return {(self.i0 + i, self.j0 + j) for i in range(self.nx) for j in range(self.ny)}


def towers_of(spec) -> list[Tower]:
    txt = spec.towers.strip()
    if not txt:
        return [Tower(1, 0, 0, spec.bays, spec.travei, spec.stories)]
    out: list[Tower] = []
    for k, tok in enumerate((t.strip() for t in txt.split(";") if t.strip()), 1):
        try:
            i0, j0, nx, ny, st = (int(x) for x in tok.split(","))
        except ValueError as e:
            raise GenError(f"Turn „{tok}”: folosește formatul i0,j0,nx,ny,etaje (ex. 0,0,3,3,8;4,0,3,3,12).") from e
        if not (0 <= i0 and 0 <= j0 and nx >= 1 and ny >= 1 and i0 + nx <= spec.bays and j0 + ny <= spec.travei):
            raise GenError(f"Turn „{tok}”: dreptunghiul iese din grilă ({spec.bays}×{spec.travei} celule).")
        if not 1 <= st <= 60:
            raise GenError(f"Turn „{tok}”: numărul de etaje trebuie să fie între 1 și 60.")
        out.append(Tower(k, i0, j0, nx, ny, st))
    for a in range(len(out)):
        for b in range(a + 1, len(out)):
            if out[a].cells & out[b].cells:
                raise GenError(f"Turnurile {a + 1} și {b + 1} se suprapun.")
    if len(out) > 1:
        for t in out:
            t.prefix = f"T{t.index}_"
    return out


def above_count(spec) -> int:
    """Numarul de etaje peste teren al modelului (cel mai inalt turn)."""
    return max(t.stories for t in towers_of(spec))
