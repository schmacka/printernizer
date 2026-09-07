info = { id = "s7b_stamp_midheight", type = "project.plugin",
         title = "S7b: stamp at mid-height (z=5) instead of the first layer",
         menu = "Spike/S7b Stamp midheight" }

function execute(opts)
    -- A 10 mm tall cube so z=5 is a real interior layer boundary.
    api.project:add_object{ mesh = api.make_cube(20, 20, 10) }

    local bed = api.project:current_bed()

    -- layer_height IS a plain number (temp_tower.lua does arithmetic on it);
    -- first_layer_height came back as opaque userdata in S7.
    local lh = 0.2
    local ok, v = pcall(function() return bed:print_presets():value("layer_height") end)
    if ok and type(v) == "number" and v > 0 then lh = v end
    print("S7b layer_height type=" .. type(v) .. " value=" .. tostring(v))

    -- Three heights, so we learn WHERE it sticks rather than just whether.
    api.project:insert_layer_custom_gcode(bed, lh,      "; PRINTERNIZER_AT=layer1")
    api.project:insert_layer_custom_gcode(bed, 2.0,     "; PRINTERNIZER_AT=z2")
    api.project:insert_layer_custom_gcode(bed, 5.0,     "; PRINTERNIZER_AT=z5")
end
