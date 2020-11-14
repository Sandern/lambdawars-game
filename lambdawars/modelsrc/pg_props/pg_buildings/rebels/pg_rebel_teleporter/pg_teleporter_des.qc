$scale 1.5
$modelname PG_props/pg_buildings/rebels/pg_teleporter_des.mdl
$cdmaterials "models/PG_props/pg_buildings/rebels"

$body pg_teleporter_des "pg_teleporter_des.smd"

$surfaceprop	metal
//$eyeposition 0 0 35
$attachment "root" "root" 0.00 0.00 0.00 rotate 0 0 0

$animation a_destruction01 "animations/pg_teleporter_des_ani" 

$sequence destruction01 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }
 