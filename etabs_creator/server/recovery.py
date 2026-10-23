"""ETABS se degradeaza dupa multe modele create la rand („Invalid pointer” la NewGridOnly): se reporneste instanta la timp sau la prima eroare COM."""
from __future__ import annotations

from typing import Callable

import comtypes

from ..connect import GenError, start_etabs
from .state import STATE

MAX_BUILDS = 8                                  # modele create cu aceeasi instanta inainte de repornire preventiva


def restart_etabs() -> None:
    """Inchide instanta (daca raspunde) si porneste una noua; contorul de modele se reseteaza."""
    obj = STATE["obj"]
    if obj is not None:
        try:
            obj.ApplicationExit(False)
        except Exception:
            pass
    STATE["obj"] = start_etabs()
    STATE["builds"] = 0


def build_with_recovery(fn: Callable[[], dict], restart: Callable[[], None] = restart_etabs, max_builds: int = MAX_BUILDS) -> dict:
    """Ruleaza `fn` (construirea modelului). Reporneste ETABS preventiv dupa `max_builds` modele si, o singura data, la o eroare COM."""
    if STATE.get("builds", 0) >= max_builds:
        restart()
    try:
        out = fn()
    except (comtypes.COMError, OSError) as first:
        try:
            restart()
            out = fn()
        except (comtypes.COMError, OSError) as second:
            raise GenError(f"ETABS nu mai răspunde nici după repornire ({second}); prima eroare: {first}.") from second
    STATE["builds"] = STATE.get("builds", 0) + 1
    return out
