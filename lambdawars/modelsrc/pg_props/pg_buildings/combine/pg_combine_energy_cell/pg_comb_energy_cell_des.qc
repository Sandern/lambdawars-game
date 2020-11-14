$scale 1.2
$modelname PG_props/pg_buildings/combine/pg_combine_energy_cell_des.mdl
$cdmaterials "models/PG_props/pg_buildings/combine" 

$body pg_comb_energy_cell_des "pg_comb_energy_cell_des.smd"

$surfaceprop	metal
$eyeposition 0 0 75

$attachment "root" "building" -45.00 0.00 0.00 rotate 0 0 0

$animation a_destruction01 "pg_comb_energy_cell_des_ani" 


$sequence destruction01 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }
