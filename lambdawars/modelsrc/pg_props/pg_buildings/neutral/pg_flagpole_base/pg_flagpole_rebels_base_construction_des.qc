$scale 1.9
$modelname pg_props/pg_buildings/other/pg_flagpole_base/pg_flagpole_rebels_base_construction_des.mdl
$cdmaterials models/pg_props/pg_buildings/other/pg_flagpole_base

$body pg_flagpole_rebels_base_construction_des "pg_flagpole_rebels_base_construction_des.smd"

$surfaceprop	wood

$animation a_destruction01 "pg_flagpole_rebels_base_construction_des_ani" 

$sequence destruction01 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }

