"""
Parametric vase template (build123d).

A round (or faceted) vase with configurable taper, twist and wall thickness.
The body is built by lofting a stack of scaled/rotated profiles, which handles
taper, faceting and twist uniformly. ``build`` returns a build123d part that the
generator engine exports to STL.
"""
from build123d import (
    Circle,
    Plane,
    Pos,
    RegularPolygon,
    Rot,
    loft,
)

# Number of cross-sections lofted along the height. More sections give a
# smoother twist at the cost of a heavier mesh.
_SECTIONS = 32


def _profile(radius: float, angle: float, facets: int):
    """A single cross-section sketch at the XY origin, rotated by ``angle``."""
    sketch = RegularPolygon(radius, facets) if facets >= 3 else Circle(radius)
    return Rot(0, 0, angle) * sketch


def _body(base_radius: float, height: float, top_scale: float,
          twist: float, facets: int):
    """Loft a tapering/twisting solid from base_radius up to base_radius*top_scale."""
    sections = []
    for i in range(_SECTIONS + 1):
        t = i / _SECTIONS
        radius = max(0.5, base_radius * (1.0 + (top_scale - 1.0) * t))
        angle = twist * t
        sections.append(Plane.XY.offset(height * t) * _profile(radius, angle, facets))
    return loft(sections)


def build(
    diameter: float = 60.0,
    height: float = 120.0,
    wall_thickness: float = 2.0,
    top_scale: float = 0.7,
    facets: int = 0,
    twist: float = 0.0,
    **_ignored,
):
    """Build a parametric vase with a solid floor of ``wall_thickness``."""
    facets = int(facets or 0)
    base_radius = diameter / 2.0

    outer = _body(base_radius, height, top_scale, twist, facets)
    cavity = _body(base_radius - wall_thickness, height, top_scale, twist, facets)
    # Lift the cavity to leave a solid floor.
    cavity = Pos(0, 0, wall_thickness) * cavity

    return outer - cavity
