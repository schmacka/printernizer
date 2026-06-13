// Parametric Vase Generator
// A configurable round vase with optional twist and faceting.

/* [Dimensions] */
// Total height of the vase (mm)
height = 120;          // [40:300]
// Radius at the base (mm)
base_radius = 40;      // [15:120]
// Radius at the top opening (mm)
top_radius = 30;       // [10:120]
// Wall thickness (mm)
wall_thickness = 2;    // [0.8:0.2:6]

/* [Style] */
// Twist applied over the full height (degrees)
twist = 60;            // [0:360]
// Number of sides (low values give a faceted look)
sides = 64;            // [3, 6, 8, 12, 24, 48, 64, 128]
// Add a solid closed bottom
closed_bottom = true;

/* [Quality] */
// Curve smoothness
$fn = 64;              // [16:8:200]

module vase() {
    difference() {
        // Outer body
        linear_extrude(height = height, twist = twist, slices = max(1, height))
            circle(r = base_radius, $fn = sides);

        // Hollow interior (leave wall_thickness)
        translate([0, 0, closed_bottom ? wall_thickness : -1])
            linear_extrude(
                height = height - (closed_bottom ? wall_thickness : 0) + 1,
                twist = twist,
                slices = max(1, height))
                circle(r = base_radius - wall_thickness, $fn = sides);
    }
}

// Scale the top to create taper from base_radius to top_radius.
module tapered_vase() {
    scale_top = top_radius / base_radius;
    // Approximate taper using a hull of base and top profiles is expensive;
    // a simple linear_extrude with scale gives a clean cone-like taper.
    difference() {
        linear_extrude(height = height, twist = twist, scale = scale_top,
                       slices = max(1, height))
            circle(r = base_radius, $fn = sides);
        translate([0, 0, closed_bottom ? wall_thickness : -1])
            linear_extrude(
                height = height - (closed_bottom ? wall_thickness : 0) + 1,
                twist = twist, scale = scale_top, slices = max(1, height))
                circle(r = base_radius - wall_thickness, $fn = sides);
    }
}

tapered_vase();
