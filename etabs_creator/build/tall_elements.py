"""Elementele unui nivel al turnului: pereti cu centura dummy, stalpi, grinzi, placi (cu setul de incarcari), pereti de subsol pe contur, spire."""
from __future__ import annotations

from ..connect import ok
from ..tall.levels import TLevel
from ..tall.storyplan import StoryPlan
from .context import Ctx
from .tall_sections import TallSections

FACADE_KINDS = ("perim", "tip")
GRAVITY = 10
PIERS = tuple([f"SP{w}{s}" for w in range(3) for s in "LR"] + [f"CORE{2 * w}{s}" for w in range(3) for s in "LR"] + [f"CORE{i}" for i in (1, 3, 5)])


def define_piers(c: Ctx) -> None:
    for p in PIERS:
        c.sap.PierLabel.SetPier(p)


def _belt(c: Ctx, ts: TallSections, lv: TLevel, a, b) -> None:
    c.beams.append(c.add_frame((*a, lv.z_top), (*b, lv.z_top), ts.belt, "centură"))
    c.bump("centuri")


def walls(c: Ctx, ts: TallSections, lv: TLevel, sp: StoryPlan, prop: str, first: bool) -> None:
    for w in sp.walls:
        name = c.add_poly([(*w.a, lv.z_bot), (*w.b, lv.z_bot), (*w.b, lv.z_top), (*w.a, lv.z_top)], prop, "perete")
        ok(c.sap.AreaObj.SetPier(name, w.pier), "AreaObj.SetPier")
        c.pier_areas.append((name, w.pier))
        c.bump("pereti")
        if first:
            c.restrain_panel_base(name)
        _belt(c, ts, lv, w.a, w.b)


def basement_outline(c: Ctx, ts: TallSections, lv: TLevel, sp: StoryPlan, first: bool) -> None:
    """Pereti perimetrali de subsol pe conturul in Y (conturul e antiorar: axa locala 3 a panoului e spre exterior)."""
    for a, b in sp.outline:
        name = c.add_poly([(*a, lv.z_bot), (*b, lv.z_bot), (*b, lv.z_top), (*a, lv.z_top)], ts.bwall, "perete subsol")
        c.bump("pereti_subsol")
        c.soil_areas.append((name, "free", "out"))
        if first:
            c.restrain_panel_base(name)
        _belt(c, ts, lv, a, b)


def columns(c: Ctx, lv: TLevel, sp: StoryPlan, prop: str) -> None:
    for p in sp.columns:
        c.frames.append(c.add_frame((*p, lv.z_bot), (*p, lv.z_top), prop, "stâlp"))
        c.bump("stalpi")


def beams(c: Ctx, lv: TLevel, sp: StoryPlan, secs: dict[str, str], facade: float, basement: bool) -> None:
    """Grinzile nivelului; la nivelurile tehnice grinzile de perimetru sunt centuri adanci. Fatada: sarcina liniara permanenta pe grinzile de perimetru."""
    h = lv.z_top - lv.z_bot
    for b in sp.beams:
        if basement and b.kind in FACADE_KINDS:
            continue                                                  # contur: peretele de subsol cu centura
        prop = secs["mbelt"] if (lv.kind == "mech" and b.kind in FACADE_KINDS) else secs["beam"]
        name = c.add_frame((*b.a, lv.z_top), (*b.b, lv.z_top), prop, f"grindă {b.kind}")
        c.frames.append(name)
        c.beams.append(name)
        c.bump("grinzi")
        if b.kind in FACADE_KINDS and facade > 0 and not basement:
            ok(c.sap.FrameObj.SetLoadDistributed(name, "Permanenta", 1, GRAVITY, 0.0, 1.0, facade * h, facade * h), "SetLoadDistributed (fațadă)")
        if b.kind in FACADE_KINDS and "Temp" in c.variable and not basement:
            ok(c.sap.FrameObj.SetLoadTemperature(name, "Temp", 1, c.spec.tall_temp), "SetLoadTemperature")


def slabs(c: Ctx, lv: TLevel, sp: StoryPlan, prop: str, load_set: str, assign: dict[str, str]) -> None:
    for poly in sp.slabs:
        name = c.add_poly([(*p, lv.z_top) for p in poly], prop, "placă")
        ok(c.sap.AreaObj.SetDiaphragm(name, "D1"), "AreaObj.SetDiaphragm")
        assign[name] = load_set
        c.slabs.append(name)
        c.bump("placi")


def spire(c: Ctx, ts: TallSections, lv: TLevel, index: int, first_base: list) -> None:
    """Un nivel de spire: teava centrata; la baza primului nivel, spite de la colturile miezului la centru (leaga catargul de miez)."""
    z0 = lv.z_bot
    if index == 0:
        for v in first_base:
            name = c.add_frame((*v, z0), (0.0, 0.0, z0), ts.spoke, "spiță")
            c.bump("spite")
            c.frames.append(name)
    name = c.add_frame((0.0, 0.0, z0), (0.0, 0.0, lv.z_top), ts.pipes[index], "catarg")
    c.frames.append(name)
    c.bump("catarg")
    if index == 0:
        c.waivers.append((f"r2_continuitate_verticala|frame:{name}", "Catargul de oțel reazemă pe spițe de transfer de la colțurile miezului (soluția constructivă a spirei), nu pe un element vertical."))
