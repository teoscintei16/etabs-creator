"""Defect de mesh: setari diferite de standard (global si pe arii)."""
from __future__ import annotations

from ..connect import GenError
from ..rules.mesh import AREA_TABLES, FLOOR_GLOBAL, WALL_GLOBAL
from ..tables import read_table, update_rows
from .registry import defect


@defect("mesh_nonstandard", "mesh global General 1.25 m, arii fara restrictii")
def mesh_nonstandard(c) -> str:
    update_rows(c.sap, FLOOR_GLOBAL, {None: {"MeshOpt": "General", "Localized": "No", "MergeJoints": "No", "MaxMeshSize": "1.25"}}, None)
    update_rows(c.sap, WALL_GLOBAL, {None: {"MaxMeshSize": "1.25"}}, None)
    for key, _opt in AREA_TABLES:
        try:
            _v, _f, rows = read_table(c.sap, key)
        except GenError:
            continue
        if rows:
            update_rows(c.sap, key, {r["UniqueName"]: {"MeshOption": "Default", "Restraints": "No"} for r in rows}, "UniqueName")
    return "mesh nestandard: General 1.25 m, fără restricții pe arii"
