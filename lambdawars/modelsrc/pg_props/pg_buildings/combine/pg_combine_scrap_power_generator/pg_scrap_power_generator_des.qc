$scale 2.4
$modelname PG_props/pg_buildings/combine/pg_scrap_power_generator_des.mdl
$cdmaterials "models/PG_props/pg_buildings/combine"

$body pg_scrap_power_generator_des "pg_scrap_power_generator_des.smd"

$surfaceprop	metal
$eyeposition 0 0 75


$animation a_destruction01 "pg_scrap_power_generator_des_ani2" 


$sequence destruction01 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }
 