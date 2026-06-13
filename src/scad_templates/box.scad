// Parametric Box Generator
// A configurable rectangular box with optional lid recess and rounded corners.

/* [Dimensions] */
// Inner width (mm)
width = 80;            // [20:300]
// Inner depth (mm)
depth = 60;            // [20:300]
// Inner height (mm)
height = 40;           // [10:300]
// Wall thickness (mm)
wall_thickness = 2;    // [1:0.5:8]

/* [Style] */
// Corner rounding radius (mm, 0 = sharp)
corner_radius = 3;     // [0:0.5:20]
// Add a solid bottom
closed_bottom = true;

/* [Quality] */
$fn = 48;              // [12:4:120]

module rounded_box(w, d, h, r) {
    if (r <= 0) {
        cube([w, d, h]);
    } else {
        hull() {
            for (x = [r, w - r], y = [r, d - r])
                translate([x, y, 0]) cylinder(h = h, r = r);
        }
    }
}

module box() {
    outer_w = width + 2 * wall_thickness;
    outer_d = depth + 2 * wall_thickness;
    outer_h = height + (closed_bottom ? wall_thickness : 0);
    difference() {
        rounded_box(outer_w, outer_d, outer_h, corner_radius);
        translate([wall_thickness, wall_thickness, closed_bottom ? wall_thickness : -1])
            rounded_box(width, depth, height + 1, max(0, corner_radius - wall_thickness));
    }
}

box();
