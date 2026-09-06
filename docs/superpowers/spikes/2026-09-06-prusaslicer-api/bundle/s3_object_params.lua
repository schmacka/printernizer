info = {
    id = "s3_object_params",
    type = "project.plugin",
    title = "S3b: settings via object_params (25 mm cube)",
    menu = "Spike/S3 Object params",
}

function execute(opts)
    api.project:add_object{ mesh = api.make_cube(5, 5, 5) }
    api.project:add_object{
        mesh = api.make_cube(25, 25, 25),
        object_params = {
            layer_height = 0.3,
            fill_density = "55%",
            perimeters = 6,
            fill_pattern = "gyroid",
            brim_type = "outer_only",
        },
    }
end
