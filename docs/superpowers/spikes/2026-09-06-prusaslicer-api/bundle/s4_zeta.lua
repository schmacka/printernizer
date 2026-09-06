info = { id = "s4_zeta", type = "project.plugin",
         title = "S4: zeta (file written 1st)", menu = "Spike/S4 Order/zeta" }
function execute(opts)
    api.project:add_object{ mesh = api.make_cube(30, 10, 10) }
end
