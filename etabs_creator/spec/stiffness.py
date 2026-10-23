"""Rigiditatea si setarile de analiza: fisurare, zone rigide, mesh, moduri."""
from __future__ import annotations

from dataclasses import dataclass

from ..connect import GenError


@dataclass
class StiffnessSpec:
    crack_col_I: float = 0.7                # fisurare (EC8 / P100-1): factori pe sectiuni
    crack_col_J: float = 0.1
    crack_beam_I: float = 0.5
    crack_beam_J: float = 0.1
    crack_slab: float = 0.5                 # m11 = m22 = m12
    rigid_zone: float = 0.75                # factorul zonei rigide la capete
    mesh_max: float = 0.5                   # m, dimensiunea maxima aproximativa a elementelor
    mesh_floor: str = "auto"                # optiunea de mesh a placilor: auto (General la plan liber, altfel Rectangular) | Rectangular | General
    modes_total: int = 0                    # > 0: numarul total de moduri/vectori (in loc de „pe etaj”: la cladiri foarte inalte)
    modal_type: str = "eigen"               # cazul modal „Modal”: eigen | ritz (vectori Ritz din acceleratii: masa participanta mult mai repede la structuri cu multe moduri locale)
    modes_per_story: int = 3                # moduri pe etaj PESTE TEREN (subsolul rigid nu vibreaza)

    def validate(self) -> None:
        for f in ("crack_col_I", "crack_col_J", "crack_beam_I", "crack_beam_J", "crack_slab", "rigid_zone"):
            if not 0 < getattr(self, f) <= 1:
                raise GenError(f"„{f}” trebuie să fie între 0 (exclusiv) și 1.")
        if self.mesh_floor not in ("auto", "Rectangular", "General"):
            raise GenError("Mesh-ul plăcilor: auto, Rectangular sau General.")
        if self.modes_total < 0:
            raise GenError("Numărul total de moduri nu poate fi negativ.")
        if self.modal_type not in ("eigen", "ritz"):
            raise GenError("Cazul modal: eigen sau ritz.")
        if self.mesh_max <= 0 or self.modes_per_story < 1:
            raise GenError("Dimensiunea mesh-ului și numărul de moduri pe etaj trebuie să fie pozitive.")
