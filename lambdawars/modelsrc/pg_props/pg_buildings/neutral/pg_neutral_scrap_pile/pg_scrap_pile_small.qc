$scale 3.0
$modelname PG_props/pg_buildings/pg_scrap_pile_small.mdl
$cdmaterials "models/PG_props/pg_buildings"

$body pg_scrap_pile_small "pg_scrap_pile_small.smd"

$surfaceprop	metal



$sequence idle {
pg_scrap_pile_small
activity ACT_IDLE 1
 }
 

$collisionmodel "pg_scrap_pile_small_phy.smd"
{
$Mass 150
$concave
} 