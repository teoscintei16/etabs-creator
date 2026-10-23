"""Coji sferice cu coaste (Opera din Sydney): geometrie pura a petecelor de sfera si reteaua lor."""
from .mesh import ShellMesh, build_mesh
from .sphere import point_on, sphere_center

__all__ = ["ShellMesh", "build_mesh", "point_on", "sphere_center"]
