$scale 1.8
$modelname PG_props/pg_buildings/combine/pg_synth_factory_des.mdl
$cdmaterials "models/PG_props/pg_buildings/combine" 

$body pg_synth_factory_des "pg_synth_factory_des.smd"

$surfaceprop	metal
$eyeposition 0 0 75

$animation a_destruction01 "pg_synth_factory_ex_ani" 


$sequence destruction01 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }
