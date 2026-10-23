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
    names = {k: (v if isinstance(v, list) else [v]) for k, v in names.items()}        # o cheie poate avea mai multe sectiuni (zone de inaltime)
    notes = [f"stâlpi I×{spec.crack_col_I:g}/J×{spec.crack_col_J:g}", f"grinzi I×{spec.crack_beam_I:g}/J×{spec.crack_beam_J:g}",
             f"plăci m×{spec.crack_slab:g}"]
    for n in names["column"]:
        ok(sap.PropFrame.SetModifiers(n, _frame_mods(spec.crack_col_J, spec.crack_col_I)), "PropFrame.SetModifiers (stâlp)")
    for n in names["beam"]:
        ok(sap.PropFrame.SetModifiers(n, _frame_mods(spec.crack_beam_J, spec.crack_beam_I)), "PropFrame.SetModifiers (grindă)")
    s = spec.crack_slab
    for n in names["slab"]:
        ok(sap.PropArea.SetModifiers(n, _shell_mods(1.0, s)), "PropArea.SetModifiers (placă)")
    if "cbeam" in names:                  # grinzi de cuplare: ca grinzile obisnuite
        for n in names["cbeam"]:
            ok(sap.PropFrame.SetModifiers(n, _frame_mods(spec.crack_beam_J, spec.crack_beam_I)), "PropFrame.SetModifiers (cuplare)")
        notes.append("grinzi de cuplare ca grinzile")
    for key, what in (("bwall", "pereți de subsol"), ("wall", "pereți")):
        if key in names:
            for n in names[key]:
                ok(sap.PropArea.SetModifiers(n, _shell_mods(spec.crack_wall_f, spec.crack_wall_m)), f"PropArea.SetModifiers ({what})")
            notes.append(f"{what} f×{spec.crack_wall_f:g}/m×{spec.crack_wall_m:g}")
    if "belt" in names:                   # centura dummy: fara masa si greutate (peretele le are deja)
        for n in names["belt"]:
            ok(sap.PropFrame.SetModifiers(n, _frame_mods(1.0, 1.0, mass=0.0)), "PropFrame.SetModifiers (centură)")
        notes.append("centuri dummy fără masă")
    return "fisurare: " + ", ".join(notes)
