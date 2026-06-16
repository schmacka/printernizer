"""
Parametric box template (build123d).

A rectangular open/closed box with configurable inner dimensions, wall
thickness and rounded corners. ``build`` returns a build123d part that the
generator engine exports to STL.
"""
from build123d import (
    Pos,
    Rectangle,
    RectangleRounded,
    extrude,
)


def _shell(width: float, depth: float, height: float, radius: float):
    """Solid (optionally round-cornered) block centered on the XY origin."""
    if radius and radius > 0:
        # Clamp the radius so it never exceeds half of the shorter side.
        r = min(radius, min(width, depth) / 2.0 - 0.001)
        sketch = RectangleRounded(width, depth, max(r, 0.001))
    else:
        sketch = Rectangle(width, depth)
    return extrude(sketch, amount=height)


def build(
    width: float = 80.0,
    depth: float = 60.0,
    height: float = 40.0,
    wall_thickness: float = 2.0,
    corner_radius: float = 3.0,
    closed_bottom: bool = True,
    **_ignored,
):
    """Build a parametric box. Inner cavity is hollowed from the outer shell."""
    outer_w = width + 2.0 * wall_thickness
    outer_d = depth + 2.0 * wall_thickness
    outer_h = height + (wall_thickness if closed_bottom else 0.0)

    outer = _shell(outer_w, outer_d, outer_h, corner_radius)

    inner_radius = max(0.0, corner_radius - wall_thickness)
    cavity = _shell(width, depth, height + 1.0, inner_radius)
    # Lift the cavity to leave a solid floor when closed_bottom is set.
    cavity = Pos(0, 0, wall_thickness if closed_bottom else -1.0) * cavity

    return outer - cavity
