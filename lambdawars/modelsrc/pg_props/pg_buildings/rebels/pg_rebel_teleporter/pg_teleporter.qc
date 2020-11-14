$scale 1.5
$modelname PG_props/pg_buildings/rebels/pg_teleporter.mdl
$cdmaterials "models/PG_props/pg_buildings/rebels" "models/PG_props/pg_buildings/" 

$body pg_teleporter "pg_teleporter_v2.smd"
$body pg_teleporter_gates01 "pg_teleporter_gates01.smd"
$body pg_teleporter_gates02 "pg_teleporter_gates02.smd"
$bodygroup construction
{
	studio "pg_teleporter_construction.smd"
	blank
}

$lod 100
{
	replacemodel "pg_teleporter_v2.smd" "pg_teleporter_low.smd"
	replacemodel "pg_teleporter_gates01.smd" "pg_teleporter_gates01_low.smd"
	replacemodel "pg_teleporter_gates02.smd" "pg_teleporter_gates02_low.smd"
	bonetreecollapse "gate_gear001"
	bonetreecollapse "gate_gear002"
	bonetreecollapse "gate_gear003"
	bonetreecollapse "gate_gear004"
	bonetreecollapse "gate_gear005"
	bonetreecollapse "gate_gear006"
	bonetreecollapse "gate_gear007"
	bonetreecollapse "gate_gear008"
	bonetreecollapse "gate_gear009"
	bonetreecollapse "gate_gear010"
	bonetreecollapse "gate_gear011"
	bonetreecollapse "gate_gear012"
	
	bonetreecollapse "charge_spin"
	bonetreecollapse "charge_spin001"
	bonetreecollapse "charge_spin002"
	bonetreecollapse "charge_spin003"
	bonetreecollapse "charge_spin004"
	bonetreecollapse "charge_spin005"
	bonetreecollapse "charge_spin006"
	bonetreecollapse "charge_spin007"
	bonetreecollapse "charge_spin008"
	bonetreecollapse "charge_spin009"
	bonetreecollapse "charge_spin010"
	bonetreecollapse "charge_spin011"
}

$surfaceprop metal
$attachment "root" "root" 0.00 0.00 0.00 rotate 90 0 0

$attachment "ring3" "ring003"  0.00 0.00 0.00 rotate 90 0 0
$attachment "ring2" "ring002"  0.00 0.00 0.00 rotate 90 0 0
$attachment "ring1" "ring001"  0.00 0.00 0.00 rotate 90 0 0

 //-- ANIMATION --
$animation a_idle "animations/pg_teleporter_idle"  
$animation a_idle_closed "animations/pg_teleporter_closed"  
$animation a_open "animations/pg_teleporter_open"  
$animation a_close "animations/pg_teleporter_close"  
$animation a_deployed "animations/pg_teleporter_build" 
$animation a_teleport "animations/pg_teleporter_tele" 

$animation a_spinup "animations/pg_teleporter_spinup" 
$animation a_spin "animations/pg_teleporter_spin" 
$animation a_spindown "animations/pg_teleporter_spindown" 

$animation a_p0 "animations/pg_teleporter_p0" loop fps 30 subtract a_idle 0 noanimation
$animation a_p1 "animations/pg_teleporter_p1" loop fps 30 subtract a_idle 0
$animation a_p2 "animations/pg_teleporter_p2" loop fps 30 subtract a_idle 0
$animation a_p3 "animations/pg_teleporter_p3" loop fps 30 subtract a_idle 0

$sequence progress {
	a_p0 a_p1 a_p2 a_p3
	blendwidth 4
	blend progress 0 3
	fps 30 loop
	delta
	autoplay
	hidden
 }
 
$sequence idle {
	a_idle
	loop
	activity ACT_IDLE 1
 }
 
$sequence idleClosed {
	a_idle_closed
	loop
	activity ACT_IDLE_CLOSED 1
 }
 
$sequence open {
	a_open
	activity ACT_OPEN 1
 }
 
$sequence close {
	a_close
	activity ACT_CLOSE 1
 }

$sequence deployed {
	a_deployed
	activity ACT_CONSTRUCTION 1
 }

$sequence teleport {
	a_teleport
	activity ACT_TELEPORT 1
 }

$sequence spinup {
	"animations/pg_teleporter_spinup" 
	activity ACT_SPINUP 1
 }
 
$sequence spin {
	"animations/pg_teleporter_spin" 
	loop
	activity ACT_SPIN 1
 }
 
$sequence spindown {
	"animations/pg_teleporter_spindown"
	snap
	activity ACT_SPINDOWN 1
 }

$collisionmodel  "pg_teleporter_phy.smd"
{
$Mass 650
$concave
} 