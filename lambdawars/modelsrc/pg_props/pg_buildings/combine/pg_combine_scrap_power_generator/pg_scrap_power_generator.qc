$scale 2.4
$modelname PG_props/pg_buildings/combine/pg_scrap_power_generator.mdl
$cdmaterials "models/PG_props/pg_buildings/combine"

$body pg_scrap_power_generator "pg_scrap_power_generator.smd"

$attachment "root" "root" 0.00 0.00 0.00 rotate 0 0 0
$attachment "core" "core" 0.00 0.00 0.00 rotate 0 0 0

$surfaceprop	metal


$sequence deployed {
	pg_scrap_power_generator_build
	activity ACT_CONSTRUCTION 1
 }

$sequence idle {
	pg_scrap_power_generator_idle
	loop
	activity ACT_IDLE 1
 }
 

$collisionmodel "pg_scrap_power_generator_phy.smd"
{
$Mass 150
$concave
} 