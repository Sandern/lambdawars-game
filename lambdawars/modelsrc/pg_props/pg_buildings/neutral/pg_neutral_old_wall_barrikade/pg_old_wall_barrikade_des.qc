$scale 1.0
$modelname PG_props/pg_buildings/other/pg_old_wall_barrikade_des.mdl
$cdmaterials "models/PG_props/pg_buildings/other" 

$body pg_old_wall_barrikade_des "pg_old_wall_barrikade_des.smd"

$surfaceprop	stone
$eyeposition 0 0 75

$animation a_destruction01 "pg_old_wall_barrikade_des_ani" 


$sequence destruction01 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }
 
