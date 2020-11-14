/*
==============================================================================

View model my model

==============================================================================
*/

$scale 1.0

$modelname PG_props\pg_weapons\pg_combine_sniper_w.mdl
$cdmaterials models\PG_props\pg_weapons

// whole body
$body pg_combine_sniper_w "pg_combine_sniper_w.smd" 
$attachment "fire" "fire" 0.00 0.00 0.00 rotate 0 0 0
$attachment "lazer" "lazer" 0.00 0.00 0.00 rotate 0 0 0

$surfaceprop metal


//__LOD__
$lod 35
{
      replacemodel "pg_combine_sniper_w.smd" "pg_combine_sniper_w_low.smd"
}


$sequence idle "pg_combine_sniper_w" fps 30

$jointsurfaceprop "ValveBiped.Bip01_R_Hand" "ValveBiped.Bip01_R_Hand"

$collisionmodel "pg_combine_sniper_w_phy.smd"
{
$concave
} 