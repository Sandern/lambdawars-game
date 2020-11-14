$scale 3.0
$modelname PG_props/pg_buildings/pg_scrap_pile.mdl
$cdmaterials "models/PG_props/pg_buildings"

$body pg_scrap_pile "pg_scrap_pile.smd"

$surfaceprop	metal



$sequence idle {
pg_scrap_pile
activity ACT_IDLE 1
 }
 

$collisionmodel "pg_scrap_pile_phy.smd"
{
$Mass 150
$concave
} 