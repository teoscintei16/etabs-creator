"""Stalpii si grinzile unui nivel, dupa plan."""
from __future__ import annotations

from ..connect import ok
from .context import Ctx


def columns_and_beams(c: Ctx, idx: int) -> None:
    st = c.plan.stories[idx]
    xs, ys, z0, z1 = c.xs, c.ys, st.z_bot, st.z_top
    for ix, iy in c.plan.columns(idx):
        name = c.add_frame((xs[ix], ys[iy], z0), (xs[ix], ys[iy], z1), c.sec["column"], "stâlp")
        c.frames.append(name)
        c.bump("stalpi")
        if idx == 0:
            c.base_points.append(ok(c.sap.FrameObj.GetPoints(name), "GetPoints")[0])
    bx, by = c.plan.beams(idx)
    for iy, i in bx:
        c.frames.append(c.add_frame((xs[i], ys[iy], z1), (xs[i + 1], ys[iy], z1), c.sec["beam"], "grindă X"))
        c.beams.append(c.frames[-1])
        c.bump("grinzi")
    for ix, j in by:
        c.frames.append(c.add_frame((xs[ix], ys[j], z1), (xs[ix], ys[j + 1], z1), c.sec["beam"], "grindă Y"))
        c.beams.append(c.frames[-1])
        c.bump("grinzi")
