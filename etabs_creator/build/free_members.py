"""Planul liber: stalpii (inclinati la piramide) si grinzile retelei radiale pe fiecare etaj."""
from __future__ import annotations

from ..connect import ok
from ..free import FreePlan
from .context import Ctx


def _pt(fp: FreePlan, node, level, z) -> tuple[float, float, float]:
    x, y = fp.xy(node, level)
    return x, y, z


def columns_and_beams(c: Ctx, fp: FreePlan, idx: int) -> None:
    st = fp.stories[idx]
    lo, hi = fp.levels(idx)
    for node in fp.columns(idx):
        name = c.add_frame(_pt(fp, node, lo, st.z_bot), _pt(fp, node, hi, st.z_top), c.sec["column"], "stâlp")
        c.frames.append(name)
        c.bump("stalpi")
        if idx == 0:
            c.base_points.append(ok(c.sap.FrameObj.GetPoints(name), "GetPoints")[0])
    for a, b, kind in fp.beams(idx):
        name = c.add_frame(_pt(fp, a, hi, st.z_top), _pt(fp, b, hi, st.z_top), c.sec["beam"], f"grindă {kind}")
        c.frames.append(name)
        c.beams.append(name)
        c.bump("grinzi")
