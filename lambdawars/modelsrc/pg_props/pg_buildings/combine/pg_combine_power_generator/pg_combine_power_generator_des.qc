$scale 2.0
$modelname PG_props/pg_buildings/combine/pg_combine_power_generator_des.mdl
$cdmaterials "models/PG_props/pg_buildings/combine" 

$body pg_combine_power_generator_des "pg_combine_power_generator_des.smd"

$surfaceprop	metal

$attachment "root" "root" -45.00 0.00 0.00 rotate 0 0 0

//$animation a_destruction01 "pg_combine_power_generator_des_ex" 
$animation a_destruction02 "pg_combine_power_generator_des_ex2" 


$sequence destruction01 {
	a_destruction02
	activity ACT_EXPLODE 1
	snap
 }
 
//$sequence destruction02 {
//	a_destruction01
//	activity ACT_EXPLODE 1
//	snap
 //}
 
$collisionmodel  "pg_combine_power_generator_phy.smd"
{
$Mass 650
$concave
} 