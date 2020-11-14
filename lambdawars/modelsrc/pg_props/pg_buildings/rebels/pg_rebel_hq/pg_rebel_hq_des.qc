$scale 2.5
$modelname PG_props/pg_buildings/pg_rebel_hq_des.mdl
$cdmaterials "models/PG_props/pg_buildings" "models\props_vehicles"

$body pg_rebel_hq_des "pg_rebel_hq_ex.smd"

$surfaceprop	wood
$eyeposition 0 0 75

$attachment "root" "Box001_frag_138" 0.00 0.00 0.00 rotate 0 0 0

$animation a_destruction01 "pg_rebel_hq_ex_ani" 


$sequence destruction01 {
	a_destruction01
	activity ACT_EXPLODE 1
	snap
 }
 
$collisionmodel  "pg_rebel_hq_phy.smd"
{
$Mass 650
$concave
} 