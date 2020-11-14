$scale 2.5
$modelname PG_props/pg_buildings/rebels/pg_barrel_trap_des.mdl
$cdmaterials "models/PG_props/pg_buildings/rebels" 

$body pg_rebel_hq_des "pg_barrel_trap_des.smd"

$surfaceprop	wood
$eyeposition 0 0 75

$attachment "root" "root" 0.00 0.00 0.00 rotate 0 0 0

$animation a_destruction01 "pg_barrel_trap_des_ani" 


$sequence destruction01 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }
