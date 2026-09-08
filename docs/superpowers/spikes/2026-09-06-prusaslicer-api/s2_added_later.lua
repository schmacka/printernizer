info = { id = "s2_added_later", type = "project.plugin",
         title = "S2: added after startup", menu = "Spike/S2 Added later" }
function execute(opts)
    api.project:add_object{ mesh = api.make_cube(40, 5, 5) }
end
