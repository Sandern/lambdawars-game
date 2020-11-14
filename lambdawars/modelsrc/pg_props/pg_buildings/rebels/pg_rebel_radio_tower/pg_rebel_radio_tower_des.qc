$scale 1.0
$modelname PG_props/pg_buildings/pg_rebel_radio_tower_des.mdl
$cdmaterials "models/PG_props/pg_buildings" 

$body pg_rebel_radio_tower "pg_rebel_radio_tower_ex.smd"

$surfaceprop	metal
$eyeposition 0 0 75

$attachment "root" "root" 0.00 0.00 0.00 rotate 0 0 0

$animation a_destruction01 "pg_rebel_radio_tower_ex_ani" 


$sequence idle {
	pg_rebel_radio_tower_ex
	activity ACT_IDLE 1
	snap
 }
 
 
$sequence destruction01 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }
 