info = {
    id = "s3_params",
    type = "project.plugin",
    title = "S3a: settings via params (20 mm cube)",
    menu = "Spike/S3 Params",
}

function execute(opts)
    -- Marker first: if the settings call throws, this 5 mm cube still appears
    -- and we know execute ran at all.
    api.project:add_object{ mesh = api.make_cube(5, 5, 5) }
    api.project:add_object{
        mesh = api.make_cube(20, 20, 20),
        params = {
            layer_height = 0.3,
            fill_density = "55%",
            perimeters = 6,
            fill_pattern = "gyroid",
            brim_type = "outer_only",
        },
    }
end
