$scale 2.0
$modelname PG_props/pg_buildings/combine/pg_combine_power_generator.mdl
$cdmaterials "models/PG_props/pg_buildings/combine" 

$body pg_combine_power_generator "pg_combine_power_generator.smd"

$surfaceprop	metal
$eyeposition 0 0 75

$attachment "root" "root" 0.00 0.00 0.00 rotate 0 0 0

$animation a_idle "pg_combine_power_generator_idle"   
$animation a_deployed "pg_combine_power_generator_build" 

//__LOD__
$lod 35
{
      replacemodel "pg_combine_power_generator.smd" "pg_combine_power_generator_low.smd"
}


$sequence idle {
	a_idle 
	loop
	activity ACT_IDLE 1
 }
 
$sequence deployed {
	a_deployed
	activity ACT_CONSTRUCTION 1
 }
 

$collisionmodel  "pg_combine_power_generator_phy.smd"
{
$Mass 650
$concave
} 