"""Starea serverului: firul COM unic, instanta ETABS pornita si lista modelelor create."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import comtypes
from fastapi import HTTPException

from ..connect import GenError

pool = ThreadPoolExecutor(max_workers=1, initializer=comtypes.CoInitialize)   # COM ruleaza intr-un singur fir
STATE: dict = {"obj": None, "models": []}


def run(fn, *args):
    """Executa `fn` in firul COM; GenError devine 409 cu mesajul in romana."""
    try:
        return pool.submit(fn, *args).result()
    except GenError as e:
        raise HTTPException(409, str(e)) from e


def alive() -> bool:
    if STATE["obj"] is None:
        return False
    try:
        STATE["obj"].SapModel.GetPresentUnits()
        return True
    except Exception:
        STATE["obj"] = None
        return False
