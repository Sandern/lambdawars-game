$scale 1.9
$modelname pg_props/pg_buildings/other/pg_flagpole_base/pg_flagpole_rebel_base_2.mdl
$cdmaterials models/pg_props/pg_buildings/other/pg_flagpole models/pg_props/pg_buildings/other/pg_flagpole_base

$body pg_flagpole_rebel_base_2 "pg_flagpole_rebel_base_2.smd"

$surfaceprop	concrete


$sequence idle pg_flagpole_rebel_base_2


$collisionmodel "pg_flagpole_rebel_base_2_phy.smd"
{
$Mass 150
$concave
} 