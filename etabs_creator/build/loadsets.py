"""Seturi de incarcari uniforme pe plansee (Shell Uniform Load Sets) si atribuirea lor pe arii: o singura scriere de tabel pentru toate placile."""
from __future__ import annotations

from ..tables import read_table, write_table

SETS_TABLE = "Shell Uniform Load Sets"
ASSIGN_TABLE = "Area Load Assignments - Uniform Load Sets"


def define_load_sets(sap, sets: dict[str, dict[str, float]]) -> int:
    """`sets` = {nume_set: {tipar: valoare kN/m2}}; scrie tabelul intreg. Intoarce numarul de randuri."""
    version, fields, _old = read_table(sap, SETS_TABLE)
    rows = [dict(Name=name, LoadPattern=pat, LoadValue=f"{val:g}") for name, loads in sets.items() for pat, val in loads.items()]
    write_table(sap, SETS_TABLE, version, fields, rows)
    return len(rows)


def assign_load_sets(sap, assignment: dict[str, str]) -> int:
    """`assignment` = {nume_arie: nume_set}; scrie tabelul intreg al atribuirilor."""
    version, fields, _old = read_table(sap, ASSIGN_TABLE)
    rows = [dict(UniqueName=area, LoadSet=name) for area, name in assignment.items()]
    write_table(sap, ASSIGN_TABLE, version, fields, rows)
    return len(rows)
