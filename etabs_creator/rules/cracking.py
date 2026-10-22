"""Rigiditate fisurata: modificatori pe sectiuni (EC8 / P100-1) pentru stalpi, grinzi, placi, pereti, centuri, grinzi de cuplare si pereti de subsol."""
from __future__ import annotations

from ..connect import ok


def _frame_mods(j: float, i: float, mass: float = 1.0) -> list[float]:
    """[A, As2, As3, J, I22, I33, masa, greutate]."""
    return [1.0, 1.0, 1.0, j, i, i, mass, mass]


def _shell_mods(f: float, m: float) -> list[float]:
    """[f11, f22, f12, m11, m22, m12, v13, v23, masa, greutate]."""
    return [f, f, f, m, m, m, 1.0, 1.0, 1.0, 1.0]


def apply_cracking(sap, spec, names: dict[str, str]) -> str:
    """Seteaza modificatorii pe fiecare sectiune definita (cheile din `names`: column, beam, slab, wall, belt, cbeam, bwall)."""
    notes = [f"stâlpi I×{spec.crack_col_I:g}/J×{spec.crack_col_J:g}", f"grinzi I×{spec.crack_beam_I:g}/J×{spec.crack_beam_J:g}",
             f"plăci m×{spec.crack_slab:g}"]
    ok(sap.PropFrame.SetModifiers(names["column"], _frame_mods(spec.crack_col_J, spec.crack_col_I)), "PropFrame.SetModifiers (stâlp)")
    ok(sap.PropFrame.SetModifiers(names["beam"], _frame_mods(spec.crack_beam_J, spec.crack_beam_I)), "PropFrame.SetModifiers (grindă)")
    s = spec.crack_slab
    ok(sap.PropArea.SetModifiers(names["slab"], _shell_mods(1.0, s)), "PropArea.SetModifiers (placă)")
    if "cbeam" in names:                  # grinzi de cuplare: ca grinzile obisnuite
        ok(sap.PropFrame.SetModifiers(names["cbeam"], _frame_mods(spec.crack_beam_J, spec.crack_beam_I)), "PropFrame.SetModifiers (cuplare)")
        notes.append("grinzi de cuplare ca grinzile")
    for key, what in (("bwall", "pereți de subsol"), ("wall", "pereți")):
        if key in names:
            ok(sap.PropArea.SetModifiers(names[key], _shell_mods(spec.crack_wall_f, spec.crack_wall_m)), f"PropArea.SetModifiers ({what})")
            notes.append(f"{what} f×{spec.crack_wall_f:g}/m×{spec.crack_wall_m:g}")
    if "belt" in names:                   # centura dummy: fara masa si greutate (peretele le are deja)
        ok(sap.PropFrame.SetModifiers(names["belt"], _frame_mods(1.0, 1.0, mass=0.0)), "PropFrame.SetModifiers (centură)")
        notes.append("centuri dummy fără masă")
    return "fisurare: " + ", ".join(notes)
