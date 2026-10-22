"""Nivelurile in ETABS: NewGridOnly creeaza Story1..N de la cota 0; cu subsol se redenumesc (S2, S1, P, E1…) si se pune cota bazei."""
from __future__ import annotations

from ..connect import KN_M_C, ok


def new_grid(sap, spec, plan) -> None:
    n_all = len(plan.stories)
    ok(sap.InitializeNewModel(KN_M_C), "InitializeNewModel")
    ok(sap.File.NewGridOnly(n_all, spec.story_height, spec.bottom if not spec.basement else spec.story_height,
                            spec.bays + 1, spec.travei + 1, spec.span_x, spec.span_y), "NewGridOnly")
    ok(sap.SetPresentUnits(KN_M_C), "SetPresentUnits")
    if spec.basement or len(plan.stories) != spec.stories:
        apply_story_layout(sap, plan)


def apply_story_layout(sap, plan) -> None:
    names = [s.name for s in plan.stories]
    heights = [s.height for s in plan.stories]
    n = len(names)
    ok(sap.Story.SetStories_2(plan.stories[0].z_bot, n, names, heights, [False] * n, [""] * n, [False] * n, [0.0] * n, [-1] * n),
       "Story.SetStories_2")
