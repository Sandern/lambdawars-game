$scale 1.5
$modelname PG_props/pg_buildings/other/pg_wood_fence_barricade_des.mdl
$cdmaterials "models/PG_props/pg_buildings/other" 

$body pg_wood_fence_barricade_des "pg_wood_fence_barricade_des.smd"

$surfaceprop	wood
$eyeposition 0 0 75

$animation a_destruction01 "pg_wood_fence_barricade_des_ani" 


$sequence destruction01 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }
 
