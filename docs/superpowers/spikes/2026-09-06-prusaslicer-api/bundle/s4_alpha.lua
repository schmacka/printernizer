info = { id = "s4_alpha", type = "project.plugin",
         title = "S4: alpha (file written 3rd)", menu = "Spike/S4 Order/alpha" }
function execute(opts)
    api.project:add_object{ mesh = api.make_cube(10, 10, 10) }
end
