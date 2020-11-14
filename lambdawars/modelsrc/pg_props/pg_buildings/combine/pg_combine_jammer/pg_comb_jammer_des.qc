$scale 2.0
$modelname PG_props/pg_buildings/combine/pg_combine_jammer_des.mdl
$cdmaterials "models/PG_props/pg_buildings/combine" 

$body pg_comb_jammer_des "pg_comb_jammer_des.smd"

$surfaceprop metal
$eyeposition 0 0 45

$attachment "root" "root" 0.00 0.00 0.00 rotate 0 0 0

$animation a_destruction01 "pg_comb_jammer_des_ani" 


$sequence destruction01 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }
