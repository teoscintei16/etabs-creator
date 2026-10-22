"""Materialul beton si sectiunile: stalp, grinda, placa, perete, centura, grinda de cuplare, perete de subsol."""
from __future__ import annotations

from ..connect import GenError, ok
from ..spec.sections import CONCRETE
from .context import BELT_H, CONCRETE_TYPE, SHELL_THIN, SLAB


def _cm(v: float) -> str:
    return f"{v * 100:g}"


def section_names(spec) -> dict[str, str]:
    """Numele sectiunilor care se definesc pentru acest model (cheile: material, column, beam, slab [+ wall, belt, cbeam, bwall])."""
    n = {"column": f"C{_cm(spec.column_b)}x{_cm(spec.column_h)}", "beam": f"B{_cm(spec.beam_b)}x{_cm(spec.beam_h)}",
         "slab": f"P{_cm(spec.slab_t)}", "material": spec.concrete}
    if spec.belts and (spec.walls or spec.basement):
        n["belt"] = "CENTURA"
    if spec.walls:
        n["wall"] = f"W{_cm(spec.wall_t)}"
        if spec.coupled:
            n["cbeam"] = f"CB{_cm(spec.wall_t)}x{_cm(spec.coupling_h)}"
    if spec.basement:
        n["bwall"] = f"WB{_cm(spec.basement_wall_t)}"
    return n


def define_material(sap, spec) -> str:
    n = spec.concrete
    fck, ecm = CONCRETE[n]
    ok(sap.PropMaterial.SetMaterial(n, CONCRETE_TYPE), "SetMaterial")
    ok(sap.PropMaterial.SetMPIsotropic(n, ecm, 0.2, 1e-5), "SetMPIsotropic")
    ok(sap.PropMaterial.SetWeightAndMass(n, 1, 25.0), "SetWeightAndMass")
    try:                                    # parametrii de rezistenta (nu sunt necesari analizei)
        ok(sap.PropMaterial.SetOConcrete_1(n, fck, False, 1, 2, 2, 0.002, 0.005, -0.1))
    except GenError:
        pass
    return n


def define_sections(sap, spec) -> dict[str, str]:
    """Defineste materialul si sectiunile; intoarce numele lor."""
    n = section_names(spec)
    mat = define_material(sap, spec)
    ok(sap.PropFrame.SetRectangle(n["column"], mat, spec.column_h, spec.column_b), "SetRectangle (stâlp)")
    ok(sap.PropFrame.SetRectangle(n["beam"], mat, spec.beam_h, spec.beam_b), "SetRectangle (grindă)")
    ok(sap.PropArea.SetSlab(n["slab"], SLAB, SHELL_THIN, mat, spec.slab_t), "SetSlab")
    if "wall" in n:
        ok(sap.PropArea.SetWall(n["wall"], 0, SHELL_THIN, mat, spec.wall_t), "SetWall")
    if "belt" in n:                          # centura: grinda „dummy” cat grosimea peretelui, fara masa/greutate proprie
        ok(sap.PropFrame.SetRectangle(n["belt"], mat, BELT_H, spec.wall_t if spec.walls else spec.basement_wall_t), "SetRectangle (centură)")
    if "cbeam" in n:
        ok(sap.PropFrame.SetRectangle(n["cbeam"], mat, spec.coupling_h, spec.wall_t), "SetRectangle (grindă de cuplare)")
    if "bwall" in n:
        ok(sap.PropArea.SetWall(n["bwall"], 0, SHELL_THIN, mat, spec.basement_wall_t), "SetWall (subsol)")
    return n
