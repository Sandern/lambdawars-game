$scale 1.8
$modelname PG_props/pg_buildings/combine/pg_combine_hq_des.mdl
$cdmaterials "models/PG_props/pg_buildings/combine" 

$body pg_combine_hq_des "pg_combine_hq_des.smd"

$surfaceprop	metal
$eyeposition 0 0 75

$attachment "root" "root" 0.00 0.00 0.00 rotate 0 0 0
$attachment "top" "top" 0.00 0.00 0.00 rotate 0 0 0

$animation a_destruction01 "pg_combine_hq_ex_ani" 


$sequence destruction01 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }
