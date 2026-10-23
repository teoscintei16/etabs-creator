"""Incarcarile turnului: seturi de incarcari uniforme pe ocupare si vantul pe inaltime (forte pe nivel in diafragma)."""
from __future__ import annotations

from ..connect import ok
from ..tall.levels import TLevel
from ..tall.storyplan import StoryPlan
from ..tall.wind import story_force
from .context import Ctx
from .loadsets import assign_load_sets, define_load_sets

WIND_TYPE, TEMPERATURE_TYPE = 6, 10


def sets_by_pattern(sets: dict[str, tuple[float, float]]) -> dict[str, dict[str, float]]:
    return {name: {"Permanenta": perm, "Live": live} for name, (perm, live) in sets.items()}


def load_sets(c: Ctx, sets: dict[str, tuple[float, float]], assign: dict[str, str]) -> str:
    n = define_load_sets(c.sap, sets_by_pattern(sets))
    m = assign_load_sets(c.sap, assign)
    return f"{len(sets)} seturi de încărcări uniforme ({n} rânduri), atribuite la {m} plăci"


def define_wind(c: Ctx) -> None:
    for name in ("Vant_X", "Vant_Y"):
        ok(c.sap.LoadPatterns.Add(name, WIND_TYPE, 0, True), f"LoadPatterns.Add ({name})")
        c.variable.append(name)


def define_temperature(c: Ctx) -> None:
    """Tiparul de temperatura (cladire lunga in plan): se asigneaza grinzilor de perimetru (vezi tall_elements.beams)."""
    if c.spec.tall_temp > 0:
        ok(c.sap.LoadPatterns.Add("Temp", TEMPERATURE_TYPE, 0, True), "LoadPatterns.Add (Temp)")
        c.variable.append("Temp")


def story_wind(c: Ctx, lv: TLevel, point: tuple[float, float], width: tuple[float, float]) -> None:
    """Forta de vant pe nivel (X si Y) in punctul `point` al diafragmei, plus momentul care o aduce in centrul planului (fara torsiune parazita).
    `width` = (latime pe X, latime pe Y): vantul pe X actioneaza pe latimea de pe Y si invers."""
    spec = c.spec
    z_mid, h = (lv.z_bot + lv.z_top) / 2, lv.z_top - lv.z_bot
    fx = story_force(z_mid, h, width[1], spec.tall_wind_q10, spec.tall_wind_alpha, spec.tall_wind_cf)
    fy = story_force(z_mid, h, width[0], spec.tall_wind_q10, spec.tall_wind_alpha, spec.tall_wind_cf)
    x0, y0 = point
    name = ok(c.sap.PointObj.AddCartesian(x0, y0, lv.z_top), "PointObj.AddCartesian (vânt)")[0]
    ok(c.sap.PointObj.SetLoadForce(name, "Vant_X", [fx, 0.0, 0.0, 0.0, 0.0, y0 * fx], True), "SetLoadForce (Vant_X)")
    ok(c.sap.PointObj.SetLoadForce(name, "Vant_Y", [0.0, fy, 0.0, 0.0, 0.0, -x0 * fy], True), "SetLoadForce (Vant_Y)")
    c.bump("forte_vant", 2)
