"""Setarile de mesh: placi Rectangular + Localized + Merge Joints, pereti Auto Rectangular, 'Add Restraints' pe arii."""
from __future__ import annotations

from ..connect import GenError
from ..tables import read_table, update_rows

FLOOR_GLOBAL = "Analysis Options - Automatic Mesh Settings for Floors"
WALL_GLOBAL = "Analysis Options - Automatic Rectangular Mesh Options for Walls"
AREA_TABLES = (("Area Assignments - Floor Auto Mesh Options", "Default"), ("Area Assignments - Wall Auto Mesh Options", "Auto Rectangular"))


def apply_mesh(sap, mesh_max: float) -> str:
    """Pereti cu „Default” raman un singur element pe panou (si placa meshata nu se leaga de ei): de aceea „Auto Rectangular”."""
    size = f"{mesh_max:g}"
    update_rows(sap, FLOOR_GLOBAL, {None: {"MeshOpt": "Rectangular", "Localized": "Yes", "MergeJoints": "Yes", "MaxMeshSize": size}}, None)
    update_rows(sap, WALL_GLOBAL, {None: {"MaxMeshSize": size}}, None)
    for key, option in AREA_TABLES:
        try:
            _v, _f, rows = read_table(sap, key)
        except GenError:
            continue                                            # tabel inexistent (ex. model fara pereti)
        if rows:
            update_rows(sap, key, {r["UniqueName"]: {"MeshOption": option, "Restraints": "Yes"} for r in rows}, "UniqueName")
    return f"mesh: plăci Rectangular/Localized/Merge, {size} m; plăci „Default”, pereți „Auto Rectangular” + Add Restraints"
