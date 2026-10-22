"""Parametrii proiectului pentru setarile verificatorului (aceleasi valori ca in model) si calea fisierului de iesire."""
from __future__ import annotations

import re
from pathlib import Path


def project_params(spec) -> dict:
    out = {"ag": spec.ag, "gamma_I": spec.gamma_I, "beta0": spec.beta0, "Tb": spec.Tb, "Tc": spec.Tc, "Td": spec.Td, "q": spec.q,
           "lambda_mfse": spec.lam, "ecc": spec.ecc, "basement": "nu", "tip_cladire": "rezidential_pereti" if spec.walls else "rezidential_cadre"}
    if spec.basement:
        out.update({"basement": "da", "basement_stories": [f"S{k}" for k in range(1, spec.basement + 1)], "ground_story": "P"})
    return out


def default_path(spec, out_dir: Path) -> Path:
    safe = re.sub(r"[^\w\-]+", "_", spec.name).strip("_") or "model"
    return out_dir / f"{safe}_{spec.structure}_{spec.stories}et_{spec.bays}x{spec.travei}.EDB"
