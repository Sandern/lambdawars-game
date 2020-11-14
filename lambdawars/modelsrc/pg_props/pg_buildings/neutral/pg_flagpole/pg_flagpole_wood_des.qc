$scale 1.9
$modelname pg_props/pg_buildings/other/pg_flagpole/pg_flagpole_wood_des.mdl
$cdmaterials models/pg_props/pg_buildings/other/pg_flagpole

$body pg_flagpole_wood_des "pg_flagpole_wood_des.smd"

$surfaceprop	wood

$attachment "root" "root" 0.00 0.00 0.00 rotate 0 0 0
$attachment "middle" "middle" 0.00 0.00 0.00 rotate 0 0 0

$animation a_destruction01 "pg_flagpole_wood_des_ex" 
$animation a_end "pg_flagpole_wood_des_end" 

$sequence destruction01 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }

 $sequence end01 {
	a_end
	activity ACT_END 1
	snap
 }