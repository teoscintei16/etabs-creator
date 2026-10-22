"""Specificatia modelului: parti mici (grila, sectiuni, incarcari, rigiditate, seism, pereti, subsol, forma, turnuri) combinate intr-un ModelSpec.

Formularul si API-ul lucreaza cu un dictionar plat (numele campurilor sunt unice intre parti); in cod, `spec.stories` citeste direct din parte."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields

from ..connect import GenError
from .basement import BasementSpec
from .grid import GridSpec
from .loads import LoadSpec
from .sections import CONCRETE, SectionSpec
from .seismic import SeismicSpec
from .shape import ShapeSpec
from .stiffness import StiffnessSpec
from .towers import TowerSpec
from .walls import CORE_SHAPES, WallSpec

# numele partilor au prefix „p_” ca sa nu intre in conflict cu campurile plate (ex. campul `seismic`, `walls`, `basement`, `towers`, `shape`)
PARTS = {"p_grid": GridSpec, "p_sections": SectionSpec, "p_loads": LoadSpec, "p_stiffness": StiffnessSpec, "p_seismic": SeismicSpec,
         "p_walls": WallSpec, "p_basement": BasementSpec, "p_shape": ShapeSpec, "p_towers": TowerSpec}
STRUCTURES = ("cadre", "pereti_izolati", "pereti_cuplati", "dual", "nucleu", "neregulat", "turnuri")


def _field_owner() -> dict[str, str]:
    owner: dict[str, str] = {}
    for part, cls in PARTS.items():
        for f in fields(cls):
            if f.name in owner:
                raise RuntimeError(f"Câmpul „{f.name}” apare în două părți ({owner[f.name]}, {part}).")
            owner[f.name] = part
    return owner


OWNER = _field_owner()


@dataclass
class ModelSpec:
    name: str = "model"
    structure: str = "cadre"                # informativ: presetarea aleasa in formular
    p_grid: GridSpec = field(default_factory=GridSpec)
    p_sections: SectionSpec = field(default_factory=SectionSpec)
    p_loads: LoadSpec = field(default_factory=LoadSpec)
    p_stiffness: StiffnessSpec = field(default_factory=StiffnessSpec)
    p_seismic: SeismicSpec = field(default_factory=SeismicSpec)
    p_walls: WallSpec = field(default_factory=WallSpec)
    p_basement: BasementSpec = field(default_factory=BasementSpec)
    p_shape: ShapeSpec = field(default_factory=ShapeSpec)
    p_towers: TowerSpec = field(default_factory=TowerSpec)

    # ---- acces plat: spec.stories, spec.wall_t, ...
    def __getattr__(self, name: str):
        part = OWNER.get(name)
        if part is None:                       # proprietati calculate ale partilor (ex. `bottom`, `coupled`)
            for p in PARTS:
                if isinstance(getattr(PARTS[p], name, None), property):
                    return getattr(object.__getattribute__(self, p), name)
            raise AttributeError(name)
        return getattr(object.__getattribute__(self, part), name)

    def __setattr__(self, name: str, value) -> None:
        part = OWNER.get(name)
        if part is not None and "p_grid" in self.__dict__:
            setattr(self.__dict__[part], name, value)
        else:
            object.__setattr__(self, name, value)

    @classmethod
    def from_flat(cls, flat: dict) -> "ModelSpec":
        unknown = sorted(set(flat) - set(OWNER) - {"name", "structure"})
        if unknown:
            raise GenError(f"Câmpuri necunoscute: {', '.join(unknown)}")
        buckets: dict[str, dict] = {p: {} for p in PARTS}
        for k, v in flat.items():
            if k in OWNER:
                buckets[OWNER[k]][k] = v
        return cls(name=flat.get("name", "model"), structure=flat.get("structure", "cadre"),
                   **{p: PARTS[p](**buckets[p]) for p in PARTS})

    def to_flat(self) -> dict:
        out = {"name": self.name, "structure": self.structure}
        for p in PARTS:
            out.update(asdict(getattr(self, p)))
        return out

    def validate(self) -> "ModelSpec":
        if self.structure not in STRUCTURES:
            raise GenError(f"Tip de structură necunoscut: {self.structure}")
        for p in PARTS:
            getattr(self, p).validate()
        from ..plan import build_plan             # validarile care cer grila si turnurile (amplasari, goluri, nuclee)
        build_plan(self)
        return self


__all__ = ["ModelSpec", "PARTS", "OWNER", "STRUCTURES", "CONCRETE", "CORE_SHAPES"]
