info = { id = "s4_mike", type = "project.plugin",
         title = "S4: mike (file written 2nd)", menu = "Spike/S4 Order/mike" }
function execute(opts)
    api.project:add_object{ mesh = api.make_cube(20, 10, 10) }
end
