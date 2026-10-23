"""Constructia etapizata (cladiri inalte): grupuri de obiecte pe etape de executie si un caz neliniar etapizat „CONSTR” care adauga structura
etapa cu etapa si incarca obiectele adaugate cu greutatea proprie si permanentele (scurtarea axiala cumulata a stalpilor/peretilor)."""
from __future__ import annotations

from ..connect import ok
from ..tables import read_table, write_table
from .context import Ctx

CASE = "CONSTR"
ADD_STRUCTURE, LOAD_IF_ADDED = 1, 3                  # operatiile „Add Structure” si „Load Objects if Added” (eStagedOperation)
GROUP_TABLE = "Group Assignments"
TABLE_TYPE = {"Frame": "Line", "Area": "Area"}          # tipurile de obiect din tabelul de atribuiri (barele se numesc „Line”)


def stage_group(k: int) -> str:
    return f"ETAPA{k:02d}"


def define_staged(c: Ctx, patterns: tuple[str, ...] = ("Dead", "Permanenta")) -> str:
    """Creeaza grupurile (din c.members), cazul etapizat si combinatiile ULS_CONSTR / SLS_CONSTR (in c.extra_combos). Intoarce nota pentru raport."""
    sap = c.sap
    groups = list(c.members)
    n = len(groups)
    if not n:
        return ""
    for g in groups:
        ok(sap.GroupDef.SetGroup(g), f"GroupDef.SetGroup ({g})")
    version, fields, _old = read_table(sap, GROUP_TABLE)
    rows = [dict(GroupName=g, ObjectType=TABLE_TYPE[kind], UniqueName=name) for g, items in c.members.items() for kind, name in items]
    write_table(sap, GROUP_TABLE, version, fields, rows)
    st = sap.LoadCases.StaticNonlinearStaged
    ok(st.SetCase(CASE), "StaticNonlinearStaged.SetCase")
    ok(st.SetStageDefinitions_2(CASE, n, [1.0] * n, [i == n - 1 for i in range(n)], [""] * n, [""] * n), "SetStageDefinitions_2")
    k = len(patterns)
    for i, g in enumerate(groups, 1):
        ok(st.SetStageData_2(CASE, i, 1 + k, [ADD_STRUCTURE] + [LOAD_IF_ADDED] * k, ["Group"] * (1 + k), [g] * (1 + k), [0.0] * (1 + k),
                             [""] + ["Load"] * k, [""] + list(patterns), [1.0] * (1 + k)), f"SetStageData_2 (etapa {i})")
    gg, gq = c.spec.gamma_g, c.spec.gamma_q
    c.extra_combos += [(f"ULS_{CASE}", [(CASE, gg), ("Live", gq)]), (f"SLS_{CASE}", [(CASE, 1.0), ("Live", 1.0)])]
    return f"construcție etapizată „{CASE}”: {n} etape, {len(rows)} obiecte în grupuri; combinații ULS_{CASE}, SLS_{CASE}"
