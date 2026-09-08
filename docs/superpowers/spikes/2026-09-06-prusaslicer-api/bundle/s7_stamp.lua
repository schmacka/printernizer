info = { id = "s7_stamp", type = "project.plugin",
         title = "S7: provenance stamp + load_stl", menu = "Spike/S7 Stamp" }

function execute(opts)
    -- Marker first: proves execute ran even if a later call aborts.
    api.project:add_object{ mesh = api.make_cube(20, 20, 10) }

    -- Flat asset load (Prusa's own plugins do exactly this).
    api.project:add_object{ mesh = api.load_stl("probe.stl") }

    local bed = api.project:current_bed()

    -- What type does first_layer_height come back as? print() goes to stdout;
    -- start PrusaSlicer from a terminal to see it.
    local ok, v = pcall(function() return bed:print_presets():value("first_layer_height") end)
    print("S7 first_layer_height ok=" .. tostring(ok) .. " type=" .. type(v) .. " value=" .. tostring(v))

    local z = 0.2
    if ok and type(v) == "number" and v > 0 then z = v end

    api.project:insert_layer_custom_gcode(bed, z,
        "; PRINTERNIZER_SRC=spike123\n; PRINTERNIZER_BUSINESS=1")
end
