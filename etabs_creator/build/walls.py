"""Peretii peste teren: panouri cu eticheta Pier, centuri dummy deasupra si grinzi de cuplare cu eticheta Spandrel."""
from __future__ import annotations

from ..connect import ok
from .context import Ctx


def wall_panels(c: Ctx, idx: int) -> None:
    """Un panou pe segment de grila si pe etaj; aceeasi eticheta Pier la toate etajele si la toate panourile aceluiasi perete."""
    st = c.plan.stories[idx]
    for w in c.plan.wall_panels(idx):
        name, px, py = c.add_panel(w["axis"], w["line"], w["bay"], st.z_bot, st.z_top, c.sec["wall"], "perete")
        ok(c.sap.AreaObj.SetPier(name, w["pier"]), "AreaObj.SetPier")
        c.bump("pereti")
        if idx == 0:
            c.restrain_panel_base(name)
        if "belt" in c.sec:
            c.beams.append(c.add_frame((px[0], py[0], st.z_top), (px[1], py[1], st.z_top), c.sec["belt"], "centură"))
            c.bump("centuri")


def define_piers(c: Ctx) -> None:
    for pier in dict.fromkeys(r["pier"] for r in c.plan.runs):
        c.sap.PierLabel.SetPier(pier)              # eroare daca exista deja: se ignora


def coupling_beams(c: Ctx, idx: int) -> None:
    """Grinda de cuplare in deschiderea dintre doi pereti; eticheta Spandrel multi-etaj, definita o singura data."""
    z = c.plan.stories[idx].z_top
    xs, ys = c.xs, c.ys
    for cb in c.plan.coupling_beams(idx):
        if cb["axis"] == "X":
            a, b = (xs[cb["bay"]], ys[cb["line"]], z), (xs[cb["bay"] + 1], ys[cb["line"]], z)
        else:
            a, b = (xs[cb["line"]], ys[cb["bay"]], z), (xs[cb["line"]], ys[cb["bay"] + 1], z)
        name = c.add_frame(a, b, c.sec["cbeam"], "grindă de cuplare")
        c.beams.append(name)
        c.frames.append(name)
        if cb["spandrel"] not in c.spandrels:
            c.sap.SpandrelLabel.SetSpandrel(cb["spandrel"], True)
            c.spandrels.add(cb["spandrel"])
        ok(c.sap.FrameObj.SetSpandrel(name, cb["spandrel"]), "FrameObj.SetSpandrel")
        c.bump("grinzi_cuplare")
