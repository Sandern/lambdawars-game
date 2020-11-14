$scale 5.5
$modelname PG_props/pg_buildings/other/pg_rock_barricade_des.mdl
$cdmaterials "models/PG_props/pg_buildings/other" 

$body pg_rock_barricade_des "pg_rock_barricade_des.smd"

$surfaceprop	stone
$eyeposition 0 0 75

$animation a_destruction01 "pg_rock_barricade_des_ani" 


$sequence destruction01 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }
 
