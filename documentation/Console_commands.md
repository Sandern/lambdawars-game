# Console commands
These commands are unique to or relevant for Lambda Wars.

## General
    sv_cheats 0|1 - Enable or disable cheats
    wars_giveresources <ResourceName> <Amount> <Player|optional> - Give resources
    wars_build_instant - build units instantly (ignoring build times)
    unitpanel - Show a panel for spawning units
    unit_create - Create an unit from the console.
    abilitypanel - Show a panel to execute abilities.
    wars_abi - Execute an ability from the console.
    playermodifiertool - Show a panel to modify some player instance data like the color.
    attributemodifiertool - Show a panel for modifying attributes of units.
    load_gamepackage - Load a game package.
    change_ownernumber - Change your owner number. Is used to indentify which units you
    can control.
    sv_unitlimit - Controls the maximum population per player.
    wars_setgamerules - Change the gamerules.

## CPU
    wars_strategic_enable - Enable CPU Player for specific player
    wars_strategic_disable - Enable CPU Player for specific player
    wars_strategic_debugprint - Prints debug information about a CPU player

## Mapping
    wars_editor - Open tools for the flora editor and navigation mesh
    sv_fogofwar 0 - Disable fog of war
    noclip - Free fly mode

## Navigation
    recast_build - Builds the navigation mesh
    recast_draw_navmesh - Visualizes the navigation mesh
    recast_draw_nodepth - Draws the navigation mesh with no depth. Can be useful if map geometry is overlapping the mesh, but if you have multiple layers this can look confusing.
    recast_draw_trimeshslope - Visualizes the map geometry used by the build process. Useful if the navigation mesh result does not match the expected result.
    recast_build_numthreads - Max number of threads used when building navigation meshes in parallel (restricted by the number of meshes to build).
    recast_loadmapmesh - Generates the map geometry used by the build process. recast_build will do this automatically, but can be useful if you only want to visualize the generated map geometry.