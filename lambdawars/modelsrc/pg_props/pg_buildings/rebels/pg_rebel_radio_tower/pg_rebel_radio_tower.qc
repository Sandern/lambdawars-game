$scale 1.0
$modelname PG_props/pg_buildings/pg_rebel_radio_tower.mdl
$cdmaterials "models/PG_props/pg_buildings"

$body pg_rebel_radio_tower "pg_rebel_radio_tower.smd"

$surfaceprop	metal
$eyeposition 0 0 75

$attachment "root" "root" 0.00 0.00 0.00 rotate 0 0 0
$attachment "antena1" "antena1" 0.00 0.00 0.00 rotate 0 0 0
$attachment "antena2" "antena2" 0.00 0.00 0.00 rotate 0 0 0
$attachment "antena3" "antena3" 0.00 0.00 0.00 rotate 0 0 0

$animation a_idle "idle"   
$animation a_deployed "building" 


//-- ANIMATION --

$sequence idle {
	a_idle
	activity ACT_IDLE 1
 }
 
$sequence work {
	a_idle
	activity ACT_WORK 1
 }

 
$sequence deployed {
	a_deployed
	activity ACT_CONSTRUCTION 1
 }

$shadowlod 
{
	replacemodel "pg_rebel_radio_tower" "pg_rebel_radio_tower_slod"
} 

$collisionmodel  "pg_rebel_radio_tower_phy.smd"
{
$Mass 650
$concave
} 