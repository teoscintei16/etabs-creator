"""Materialele si sectiunile turnului: beton pe clase (cate o zona de inaltime), otel pentru spire (tevi), sectiuni pe zone."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..connect import GenError, ok
from ..spec.sections import CONCRETE
from ..tall.zones import Zone
from .context import BELT_H, CONCRETE_TYPE, SHELL_THIN, SLAB
from .sections import _cm

STEEL_TYPE = 1
STEEL_E, STEEL_NU, STEEL_ALPHA, STEEL_UNIT_WEIGHT = 2.1e8, 0.3, 1.2e-5, 78.5       # kN/m2, -, 1/°C, kN/m3
STEEL = "S355"
BEAM_B, BEAM_H = 0.6, 0.9                       # grinzile de cadru (m)
MECH_BELT_B, MECH_BELT_H = 1.2, 3.0             # centura nivelului tehnic (m)
SPIRE_OD_BASE, SPIRE_OD_TOP, SPIRE_T_RATIO = 2.6, 0.7, 1 / 40
SPOKE_OD, SPOKE_T = 0.9, 0.04


@dataclass
class TallSections:
    zone: dict[str, dict[str, str]] = field(default_factory=dict)      # cheia zonei -> {column, beam, mbelt, slab, wall}
    bwall: str = ""
    belt: str = ""
    pipes: list[str] = field(default_factory=list)                     # sectiunile spirei, de jos in sus
    spoke: str = ""
    all: dict[str, list[str]] = field(default_factory=dict)            # pentru fisurare: column, beam, slab, wall, bwall, belt (doar beton)

    def of(self, zone: Zone) -> dict[str, str]:
        return self.zone[zone.key]


def _define_concrete(sap, grade: str) -> None:
    fck, ecm = CONCRETE[grade]
    ok(sap.PropMaterial.SetMaterial(grade, CONCRETE_TYPE), f"SetMaterial ({grade})")
    ok(sap.PropMaterial.SetMPIsotropic(grade, ecm, 0.2, 1e-5), "SetMPIsotropic")
    ok(sap.PropMaterial.SetWeightAndMass(grade, 1, 25.0), "SetWeightAndMass")
    try:                                    # parametrii de rezistenta (nu sunt necesari analizei)
        ok(sap.PropMaterial.SetOConcrete_1(grade, fck, False, 1, 2, 2, 0.002, 0.005, -0.1))
    except GenError:
        pass


def _define_steel(sap) -> None:
    ok(sap.PropMaterial.SetMaterial(STEEL, STEEL_TYPE), "SetMaterial (otel)")
    ok(sap.PropMaterial.SetMPIsotropic(STEEL, STEEL_E, STEEL_NU, STEEL_ALPHA), "SetMPIsotropic (otel)")
    ok(sap.PropMaterial.SetWeightAndMass(STEEL, 1, STEEL_UNIT_WEIGHT), "SetWeightAndMass (otel)")


def short(grade: str) -> str:
    return grade.split("/")[0]


def define_tall_sections(sap, spec, zones: list[Zone]) -> TallSections:
    """Defineste materialele si sectiunile fiecarei zone, peretii de subsol, centura dummy si sectiunile de otel ale spirei."""
    ts = TallSections()
    cols, beams, slabs, walls, belts = [], [], [], [], []
    for grade in dict.fromkeys(z.grade for z in zones):
        _define_concrete(sap, grade)
    for z in zones:
        g = short(z.grade)
        n = {"column": f"TC{_cm(z.col)}_{g}", "beam": f"TB{_cm(BEAM_B)}x{_cm(BEAM_H)}_{g}", "mbelt": f"MB{_cm(MECH_BELT_B)}x{_cm(MECH_BELT_H)}_{g}",
             "slab": f"TP{_cm(z.slab_t)}_{g}", "wall": f"TW{_cm(z.wall_t)}_{g}"}
        ok(sap.PropFrame.SetRectangle(n["column"], z.grade, z.col, z.col), f"SetRectangle ({n['column']})")
        ok(sap.PropFrame.SetRectangle(n["beam"], z.grade, BEAM_H, BEAM_B), f"SetRectangle ({n['beam']})")
        ok(sap.PropFrame.SetRectangle(n["mbelt"], z.grade, MECH_BELT_H, MECH_BELT_B), f"SetRectangle ({n['mbelt']})")
        ok(sap.PropArea.SetSlab(n["slab"], SLAB, SHELL_THIN, z.grade, z.slab_t), f"SetSlab ({n['slab']})")
        ok(sap.PropArea.SetWall(n["wall"], 0, SHELL_THIN, z.grade, z.wall_t), f"SetWall ({n['wall']})")
        ts.zone[z.key] = n
        cols.append(n["column"]), beams.extend((n["beam"], n["mbelt"])), slabs.append(n["slab"]), walls.append(n["wall"])
    first = zones[0]
    ts.bwall = f"TWB{_cm(spec.basement_wall_t)}_{short(first.grade)}"
    ok(sap.PropArea.SetWall(ts.bwall, 0, SHELL_THIN, first.grade, spec.basement_wall_t), "SetWall (subsol)")
    ts.belt = "CENTURA"                                  # grinda „dummy” cat grosimea peretelui de la baza, fara masa
    ok(sap.PropFrame.SetRectangle(ts.belt, first.grade, BELT_H, first.wall_t), "SetRectangle (centură)")
    _define_steel(sap)
    k = spec.tall_spire_levels
    for i in range(k):
        od = SPIRE_OD_BASE + (SPIRE_OD_TOP - SPIRE_OD_BASE) * (i / max(k - 1, 1))
        name = f"SPIRE{_cm(od)}"
        ok(sap.PropFrame.SetPipe(name, STEEL, od, od * SPIRE_T_RATIO), f"SetPipe ({name})")
        ts.pipes.append(name)
    ts.spoke = f"SPITA{_cm(SPOKE_OD)}"
    ok(sap.PropFrame.SetPipe(ts.spoke, STEEL, SPOKE_OD, SPOKE_T), "SetPipe (spiță)")
    ts.all = {"column": cols, "beam": beams, "slab": slabs, "wall": walls, "bwall": [ts.bwall], "belt": [ts.belt]}
    return ts
