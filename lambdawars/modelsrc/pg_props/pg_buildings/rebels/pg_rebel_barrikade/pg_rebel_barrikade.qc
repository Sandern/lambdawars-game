$scale 1.9
$modelname PG_props/pg_buildings/rebels/pg_rebel_barricade.mdl
$cdmaterials "models/PG_props/pg_buildings" "models/PG_props/pg_obj/pg_flagpole" 

$body pg_rebel_cover "pg_rebel_cover.smd"

$surfaceprop	wood

$animation a_idle "pg_rebel_cover_idle"   
$animation a_deployed "deployed" 


$sequence idle {
a_idle 
activity ACT_IDLE 1
 }
 
$sequence deployed {
a_deployed
activity ACT_CONSTRUCTION 1
 }
 

$collisionmodel "pg_rebel_cover_phy_simple.smd"
{
$Mass 150
$concave
} 