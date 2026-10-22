"""Zonele rigide la capetele barelor (factor pe toate barele, cu decalaje automate din conectivitate)."""
from __future__ import annotations

from ..tables import update_rows


def apply_rigid_zones(sap, frames: list[str], factor: float) -> str:
    """FrameObj.SetEndLengthOffset ignora factorul RZ cand AutoOffset=True, deci se scrie tabelul „End Length Offsets” (intreg, o singura aplicare)."""
    n = update_rows(sap, "Frame Assignments - End Length Offsets", {f: {"RigidFact": f"{factor:g}"} for f in frames}, "UniqueName")
    return f"zone rigide ×{factor:g} la {n} bare"
