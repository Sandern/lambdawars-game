$scale 5.5
$modelname PG_props/pg_buildings/other/pg_rock_barricade.mdl
$cdmaterials "models/PG_props/pg_buildings/other"

$body pg_rock_barricade "pg_rock_barricade.smd"

$surfaceprop rock
$eyeposition 0 0 75

$animation a_idle "pg_rock_barricade"   

//__LOD__
$lod 55
{
      replacemodel "pg_rock_barricade.smd" "pg_rock_barricade_low.smd"
}

//-- ANIMATION --
 
$sequence idle {
	a_idle
	loop
	activity ACT_IDLE 1
 }
 
 
$collisionmodel  "pg_rock_barricade_low.smd"
{
$Mass 650
$concave
} 