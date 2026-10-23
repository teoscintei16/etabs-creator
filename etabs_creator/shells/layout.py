"""Amplasarea salilor si a cojilor pe grila podiumului (calcule pure): sali cu pereti lungi pe liniile grilei, coji pe acesti pereti, perechea restaurantului."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..connect import GenError
from ..plan.stories import stories_of
from ..spec.opera import floats
from .mesh import ShellMesh, build_mesh

HALL_NAMES = ("CH", "OT", "H3", "H4", "H5", "H6")
CREST_BACK = 3.0                    # m: creasta e atat de aproape de capatul nordic al bazei (nu depaseste intervalul y al randului)


@dataclass
class Hall:
    name: str
    x0: float
    x1: float
    y0: float
    y1: float

    @property
    def axis(self) -> float:
        return (self.x0 + self.x1) / 2


@dataclass
class ShellDef:
    name: str
    hall: str                       # numele salii („REST” pentru restaurant)
    side: str                       # W | E (partea fata de axa)
    row: int
    a: tuple[float, float, float]
    b: tuple[float, float, float]
    c: tuple[float, float, float]
    y0: float                       # baza fizica: y0..y1 pe linia x = foot_x
    y1: float
    foot_x: float
    on_wall: bool                   # True: baza pe peretele lung al salii; False: pe stalpii podiumului

    def mesh(self, spec) -> ShellMesh:
        return build_mesh(self.name, self.a, self.b, self.c, spec.opera_radius, spec.shell_dy, spec.shell_across, spec.shell_tip)


@dataclass
class Layout:
    z0: float                       # cota podiumului (nivelul E1)
    halls: list[Hall]
    shells: list[ShellDef]
    voids: set[tuple[int, int]] = field(default_factory=set)

    def void_text(self) -> str:
        return ";".join(f"{i},{j}" for i, j in sorted(self.voids))


def _on_grid(v: float, step: float, what: str) -> int:
    k = round(v / step)
    if abs(k * step - v) > 1e-6:
        raise GenError(f"{what} ({v:g} m) trebuie să fie pe o linie a grilei podiumului (multiplu de {step:g} m).")
    return k


def _row_shells(spec, hall: str, axis: float, half: float, y0: float, rows: list[tuple[float, float, float]], scale: float, z0: float,
                on_wall: bool) -> list[ShellDef]:
    out = []
    y = y0
    for r, (h, length, lean) in enumerate(rows, 1):
        for side, foot, sgn in (("W", axis - half, 1), ("E", axis + half, -1)):
            a = (foot, y - spec.shell_tip, z0)
            b = (foot, y + length, z0)
            c = (foot + sgn * lean, y + length - CREST_BACK, z0 + h * scale)
            out.append(ShellDef(f"SH_{hall}_{side}{r}", hall, side, r, a, b, c, y, y + length, foot, on_wall))
        y += length
    return out


def build_layout(spec) -> Layout:
    """Amplasarea completa; ridica GenError daca ceva nu se aliniaza cu grila sau nu incape pe sfera."""
    xs_max, ys_max = spec.bays * spec.span_x, spec.travei * spec.span_y
    z0 = stories_of(spec, spec.stories)[-1].z_top
    h, n, lean = (floats(getattr(spec, k), k) for k in ("shell_heights", "shell_lengths", "shell_leans"))
    rows = list(zip(h, n, lean))
    axes, scales = floats(spec.hall_axes, "hall_axes"), floats(spec.hall_scale, "hall_scale")
    if len(axes) > len(HALL_NAMES):
        raise GenError(f"Cel mult {len(HALL_NAMES)} săli.")
    if abs(spec.span_y / spec.shell_dy - round(spec.span_y / spec.shell_dy)) > 1e-9:
        raise GenError(f"Pasul rețelei cojii ({spec.shell_dy:g} m) trebuie să dividă pasul grilei pe Y ({spec.span_y:g} m).")
    length = sum(n)
    halls, shells = [], []
    for name, axis, scale in zip(HALL_NAMES, axes, scales):
        halls.append(Hall(name, axis - spec.hall_half, axis + spec.hall_half, spec.hall_y0, spec.hall_y0 + length))
        shells += _row_shells(spec, name, axis, spec.hall_half, spec.hall_y0, rows, scale, z0, True)
    if spec.restaurant:
        axis = sum(axes) / len(axes)
        shells += _row_shells(spec, "REST", axis, spec.hall_half, spec.hall_y0 + length + spec.span_y, [(spec.restaurant_height, 3 * spec.span_y,
                                                                                                       spec.restaurant_lean)], 1.0, z0, False)
    voids: set[tuple[int, int]] = set()
    for hl in halls:
        i0, i1 = _on_grid(hl.x0, spec.span_x, "Peretele lung al sălii"), _on_grid(hl.x1, spec.span_x, "Peretele lung al sălii")
        j0, j1 = _on_grid(hl.y0, spec.span_y, "Începutul sălii"), _on_grid(hl.y1, spec.span_y, "Sfârșitul sălii")
        if not (0 <= i0 < i1 <= spec.bays and 0 <= j0 < j1 <= spec.travei):
            raise GenError(f"Sala {hl.name} iese din grila podiumului ({xs_max:g} × {ys_max:g} m).")
        voids |= {(i, j) for i in range(i0, i1) for j in range(j0, j1)}
    for sh in shells:
        _on_grid(sh.foot_x, spec.span_x, f"Baza cojii {sh.name}")
        _on_grid(sh.y0, spec.span_y, f"Începutul bazei cojii {sh.name}")
        _on_grid(sh.y1, spec.span_y, f"Sfârșitul bazei cojii {sh.name}")
        if sh.y1 > ys_max + 1e-6 or not 0 <= sh.foot_x <= xs_max:
            raise GenError(f"Coaja {sh.name} iese din podium.")
        sh.mesh(spec)                                       # ridica GenError daca nu incape pe sfera
    return Layout(z0, halls, shells, voids)
