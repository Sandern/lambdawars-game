/*
==============================================================================

View model my model

==============================================================================
*/

$scale 1.0

$modelname PG_props\pg_weapons\pg_simple_hammer_w.mdl
$cdmaterials models\PG_props\pg_weapons

// whole body
$body pg_simple_hammer_w "pg_simple_hammer.smd" 

$surfaceprop metal




$sequence idle "pg_simple_hammer" fps 30

$jointsurfaceprop "ValveBiped.Bip01_R_Hand" "ValveBiped.Bip01_R_Hand"

$collisionmodel "pg_simple_hammer_phy.smd"
{
$mass 10
$concave
} 