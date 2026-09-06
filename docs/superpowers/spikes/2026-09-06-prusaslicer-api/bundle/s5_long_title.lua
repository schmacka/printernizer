info = {
    id = "s5_long_title",
    type = "project.plugin",
    title = "Benchy 3DBenchy v2 final - 12.3 MB - 0.2 mm - 1h 42m - last printed Core One, 2026-08-30",
    menu = "Spike/S5 Long title",
    params = {
        {name = "apply_settings", label = "Apply proven settings (0.2 mm - 15% - 3 perimeters)", type = "bool", default = true},
        {name = "tag", label = "Tag project for Printernizer job tracking", type = "bool", default = true},
    },
}
function execute(opts)
    api.project:add_object{ mesh = api.make_cube(10, 10, 10) }
end
