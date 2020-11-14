$scale 1.5
$modelname PG_props/pg_buildings/other/pg_wood_fence_barricade.mdl
$cdmaterials "models/PG_props/pg_buildings/other"

$body pg_wood_fence_barricade "pg_wood_fence_barricade.smd"

$surfaceprop wood
$eyeposition 0 0 75

$animation a_idle "pg_wood_fence_barricade"   


//-- ANIMATION --
 
$sequence idle {
	a_idle
	loop
	activity ACT_IDLE 1
 }
 
 
$collisionmodel  "pg_wood_fence_barricade_phy.smd"
{
$Mass 150
$concave
} 