$scale 1.0
$modelname "pg_props/pg_marks/pg_arrow.mdl"
$cdmaterials "models/PG_props/pg_marks/" 

$body pg_mark "pg_arrow.smd"

$surfaceprop	metal

$animation a_idle "pg_mark_idle"   


$sequence idle {
a_idle 
loop
activity ACT_IDLE 1
 }
 
$collisionmodel "pg_mark_phy.smd"
{
$Mass 50
$concave
} 