$scale 1.9
$modelname pg_props/pg_buildings/other/pg_flagpole_base/pg_flagpole_rebels_base_construction.mdl
$cdmaterials models/pg_props/pg_buildings/other/pg_flagpole_base

$body pg_flagpole_rebels_base_construction "pg_flagpole_rebels_base_construction.smd"

$surfaceprop	wood


$sequence idle pg_flagpole_rebels_base_construction_idle loop activity ACT_IDLE 1


$collisionmodel "pg_flagpole_rebels_base_construction_phy.smd"
{
$Mass 150
$concave
} 