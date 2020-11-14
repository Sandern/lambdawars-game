$scale 1.9
$modelname PG_props/pg_buildings/rebels/pg_rebel_mountableturret.mdl
$cdmaterials "models/PG_props/pg_buildings" "models/PG_props/pg_obj/pg_flagpole" 

$body pg_rebel_barrikade "pg_rebel_barrikade.smd"

$surfaceprop	wood

$animation a_idle "pg_rebel_barrikade_idle"   
$animation a_deployed "pg_rebel_barrikade_deployed" 
$animation a_destruction01 "pg_rebel_barrikade_ex1" 
$animation a_destruction02 "pg_rebel_barrikade_ex2" 


$sequence idle {
a_idle 
activity ACT_IDLE 1
 }
 
$sequence deployed {
a_deployed
activity ACT_CONSTRUCTION 1
 }
 
$sequence destruction01 {
a_destruction01
activity ACT_EXPLODE 1
 }
 
$sequence destruction02 {
a_destruction02
activity ACT_EXPLODE 1
 }

$collisionmodel "pg_rebel_barrikade_phy_simple.smd"
{
$Mass 150
$concave
} 