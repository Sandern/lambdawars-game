$scale 1.0
$modelname PG_props/pg_buildings/combine/pg_combine_armory_des.mdl
$cdmaterials "models/PG_props/pg_buildings/combine" 

$body pg_armory_des "pg_armory_des.smd"

$surfaceprop	metal
$eyeposition 0 0 75

$attachment "root" "building" -45.00 0.00 0.00 rotate 0 0 0

$animation a_destruction01 "pg_armory_des_ani1" 
$animation a_destruction02 "pg_armory_des_ani2" 


$sequence destruction01 {
	a_destruction02
	activity ACT_EXPLODE 1
	snap
 }
 
$sequence destruction02 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }
 
$collisionmodel  "pg_armory_phy.smd"
{
$Mass 650
$concave
} 