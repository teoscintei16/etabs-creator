"""Podiumul operei: stalpii si grinzile din interiorul salilor se omit, peretii cutiilor salilor (cu etichete Pier), grinzile de pe liniile bazei cojilor se omit."""
from __future__ import annotations

from ..connect import ok
from ..shells.layout import Layout
from .context import Ctx


def hall_voids(layout: Layout) -> tuple[set[tuple[int, int]], set[tuple[int, int]], set[tuple[int, int]]]:
    """(noduri interioare, grinzi X interioare (iy, i), grinzi Y interioare (ix, j)) ale golurilor salilor."""
    v = layout.voids
    corners = {(i + di, j + dj) for i, j in v for di in (0, 1) for dj in (0, 1)}
    nodes = {(a, b) for a, b in corners if {(a - 1, b - 1), (a, b - 1), (a - 1, b), (a, b)} <= v}
    xb = {(j, i) for i, j in v if (i, j - 1) in v}                  # grinda X pe linia j, intre celulele (i, j-1) si (i, j)
    yb = {(i, j) for i, j in v if (i - 1, j) in v}                  # grinda Y pe linia i, intre celulele (i-1, j) si (i, j)
    return nodes, xb, yb


def podium_overrides(c: Ctx, layout: Layout) -> None:
    """Completeaza c.skip_columns / c.skip_beams: in sali (peste teren) nu sunt stalpi/grinzi; pe nivelul podiumului grinzile bazei cojilor sunt inlocuite de grinda de picior."""
    spec = c.spec
    nodes, xb, yb = hall_voids(layout)
    top = max(i for i, s in enumerate(c.plan.stories) if not s.basement)
    for idx, st in enumerate(c.plan.stories):
        if st.basement:
            continue
        c.skip_columns |= {(idx, i, j) for i, j in nodes}
        c.skip_beams |= {(idx, "X", j, i) for j, i in xb} | {(idx, "Y", i, j) for i, j in yb}
    for hl in layout.halls:                                         # grinzile de pe conturul salii: inlocuite de pereti (cu centura deasupra)
        i0, i1, j0, j1 = (round(v) for v in (hl.x0 / spec.span_x, hl.x1 / spec.span_x, hl.y0 / spec.span_y, hl.y1 / spec.span_y))
        for idx in range(len(c.plan.stories)):
            c.skip_beams |= {(idx, "X", j, i) for j in (j0, j1) for i in range(i0, i1)} | {(idx, "Y", i, j) for i in (i0, i1) for j in range(j0, j1)}
    for sh in layout.shells:
        ix = round(sh.foot_x / spec.span_x)
        c.skip_beams |= {(top, "Y", ix, j) for j in range(round(sh.y0 / spec.span_y), round(sh.y1 / spec.span_y))}


def _panel(c: Ctx, pts, pier: str, belt: bool = True) -> None:
    """Panou vertical (pts: jos-stanga, jos-dreapta, sus-dreapta, sus-stanga) cu centura dummy deasupra (ca la peretii motorului)."""
    name = c.add_poly(pts, c.sec["wall"], "perete sală")
    if belt and "belt" in c.sec:
        c.beams.append(c.add_frame(pts[3], pts[2], c.sec["belt"], "centură"))
        c.bump("centuri")
    ok(c.sap.AreaObj.SetPier(name, pier), "AreaObj.SetPier")
    c.pier_areas.append((name, pier))
    c.bump("pereti")
    if pts[0][2] <= c.plan.stories[0].z_bot + 1e-6:
        c.restrain_panel_base(name)


def _cuts(a: float, b: float, step: float) -> list[float]:
    n = max(round((b - a) / step), 1)
    return [a + (b - a) * k / n for k in range(n + 1)]


def hall_walls(c: Ctx, layout: Layout) -> None:
    """Cutia fiecarei sali: 4 pereti de la baza modelului pana la nivelul podiumului; peretii lungi sunt segmentati la pasul retelei cojilor
    pe nivelul de sus (nodurile cojii coincid cu cele ale peretelui). O eticheta Pier pe latura, aceeasi la toate nivelurile."""
    spec = c.spec
    for hl in layout.halls:
        for pier in (f"{hl.name}_W", f"{hl.name}_E", f"{hl.name}_S", f"{hl.name}_N"):
            c.sap.PierLabel.SetPier(pier)
        for idx, st in enumerate(c.plan.stories):
            top = idx == len(c.plan.stories) - 1
            ys = _cuts(hl.y0, hl.y1, spec.shell_dy if top else spec.span_y)
            xs = _cuts(hl.x0, hl.x1, spec.span_x)
            for k in range(len(ys) - 1):
                for x, tag in ((hl.x0, "W"), (hl.x1, "E")):
                    _panel(c, [(x, ys[k], st.z_bot), (x, ys[k + 1], st.z_bot), (x, ys[k + 1], st.z_top), (x, ys[k], st.z_top)], f"{hl.name}_{tag}",
                           belt=not top)                            # sus, peretele lung poarta coaja: grinda de picior ia locul centurii
            for k in range(len(xs) - 1):
                for y, tag in ((hl.y0, "S"), (hl.y1, "N")):
                    _panel(c, [(xs[k], y, st.z_bot), (xs[k + 1], y, st.z_bot), (xs[k + 1], y, st.z_top), (xs[k], y, st.z_top)], f"{hl.name}_{tag}")
