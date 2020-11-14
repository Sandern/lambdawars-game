$scale 3.0
$modelname PG_props/pg_buildings/pg_scrap_pile02.mdl
$cdmaterials "models/PG_props/pg_buildings"

$body pg_scrap_pile02 "pg_scrap_pile02.smd"

$surfaceprop	metal



$sequence idle {
pg_scrap_pile02
activity ACT_IDLE 1
 }
 

$collisionmodel "pg_scrap_pile02_phy.smd"
{
$Mass 150
$concave
} 