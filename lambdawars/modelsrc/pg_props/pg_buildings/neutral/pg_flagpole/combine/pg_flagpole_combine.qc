$scale 2.4
$modelname pg_props/pg_buildings/other/pg_flagpole/pg_flagpole_combine.mdl
$cdmaterials models/pg_props/pg_buildings/other/pg_flagpole

$body pg_flagpole_combine "pg_flagpole_combine.smd"

$surfaceprop	metal

$sequence idle pg_flagpole_combine_idle loop


$collisionmodel "pg_flagpole_combine_phy.smd"
{
$Mass 150
$concave
} 