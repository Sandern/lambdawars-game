$scale 2.0
$modelname PG_props/pg_buildings/rebels/pg_junkyard_des.mdl
$cdmaterials "models/PG_props/pg_buildings/rebels"

$body pg_junkyard_des "pg_junkyard_des.smd"

$surfaceprop	wood
$eyeposition 0 0 35
$attachment "root" "root" 0.00 0.00 0.00 rotate 0 0 0

$animation a_destruction01 "pg_junkyard_des_ani" 


$sequence destruction01 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }
 