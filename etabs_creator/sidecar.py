"""Scrie parametrii proiectului si centurile in setarile verificatorului (<model>.EDB.checks.json), fara a depinde de codul lui.

Formatul e cel al verificatorului etabs-check: {"project": {...}, "belts": {"has": bool, "sections": [...]}, ...}; cheile existente se pastreaza."""
from __future__ import annotations

import json
from pathlib import Path


def sidecar_path(model_file: str) -> Path:
    """Langa model; fisierul de lucru ETABS „.$et” se inlocuieste cu „.EDB” (setarile apartin modelului salvat)."""
    if model_file.lower().endswith(".$et"):
        model_file = model_file[:-4] + ".EDB"
    return Path(model_file + ".checks.json")


def write_settings(model_file: str, project: dict, belts: dict | None = None) -> str:
    path = sidecar_path(model_file)
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
    data.setdefault("project", {}).update({k: v for k, v in project.items() if v not in (None, "", [])})
    if belts:
        data["belts"] = {"has": belts["has"], "sections": list(belts["sections"])}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return str(path)
