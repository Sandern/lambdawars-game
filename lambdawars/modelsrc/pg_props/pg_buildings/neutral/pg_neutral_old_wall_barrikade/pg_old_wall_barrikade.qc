$scale 1.0
$modelname PG_props/pg_buildings/other/pg_old_wall_barrikade.mdl
$cdmaterials "models/PG_props/pg_buildings/other"

$body pg_old_wall_barrikade "pg_old_wall_barrikade.smd"

$surfaceprop rock
$eyeposition 0 0 75

$animation a_idle "pg_old_wall_barrikade"   

//-- ANIMATION --
 
$sequence idle {
	a_idle
	loop
	activity ACT_IDLE 1
 }
 
 
$collisionmodel  "pg_old_wall_barrikade_phy.smd"
{
$Mass 650
$concave
} 