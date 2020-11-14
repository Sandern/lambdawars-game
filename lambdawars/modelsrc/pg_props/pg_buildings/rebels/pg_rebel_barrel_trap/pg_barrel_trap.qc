$scale 2.5
$modelname PG_props/pg_buildings/rebels/pg_barrel_trap.mdl
$cdmaterials "models/PG_props/pg_buildings/rebels" 

$body pg_barrel_trap "pg_barrel_trap.smd"

$surfaceprop wood
$eyeposition 0 0 75

$attachment "root" "root" 0.00 0.00 0.00 rotate 0 0 0

$animation a_idle "pg_barrel_trap_idle"   
$animation a_deployed "pg_barrel_trap_deployed" 


//-- ANIMATION --
 
$sequence idle {
	a_idle
	loop
	activity ACT_IDLE 1
 }
 
$sequence deployed {
	a_deployed
	activity ACT_CONSTRUCTION 1
 }
 

$collisionmodel  "pg_barrel_trap_phy.smd"
{
$Mass 650
$concave
} 