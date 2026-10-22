"""Structuri cu plan liber (cerc, semicerc, spline, trapez, piramide…): geometrie pura."""
from .plan import FreePlan, build_free_plan, parse_wall_edges

__all__ = ["FreePlan", "build_free_plan", "parse_wall_edges"]
