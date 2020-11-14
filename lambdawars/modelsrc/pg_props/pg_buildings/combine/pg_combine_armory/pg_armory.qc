$scale 1.0
$modelname PG_props/pg_buildings/combine/pg_combine_armory.mdl
$cdmaterials "models/PG_props/pg_buildings/combine" 

$body pg_armory "pg_armory.smd"

$surfaceprop	metal
$eyeposition 0 0 75

$attachment "root" "armory" 0.00 0.00 0.00 rotate 0 0 0
$attachment "antena" "antena_end" 0.00 0.00 0.00 rotate 0 0 0


$animation a_idle "idle"   
$animation a_deployed "build" 
$animation a_work "work" 
$animation a_p0 "p0" subtract a_idle 0 noanimation 
$animation a_p1 "p1" subtract a_idle 0 
$animation a_p2 "p2" subtract a_idle  0
$animation a_p3 "p3" subtract a_idle 0
$animation a_p4 "p4" subtract a_idle  0 


//-- ANIMATION --
$weightlist progress_waight {
energy 1.0
energy_dum 1.0
energy001 1.0
energy_dum001 1.0
energy002 1.0
energy_dum002 1.0
energy003 1.0
energy_dum003 1.0
armory 0.0
arm 0.0
arm001 0.0
arm002 0.0
arm003 0.0

arm_down002 0.0
}
 $sequence progress {
	a_p0 a_p1 a_p2 a_p3 a_p4
	blendwidth 5
	blend progress 0 100
	weightlist progress_waight
	loop
	delta
	hidden
 }

$sequence idle {
	a_idle
	addlayer progress
	
	loop
	activity ACT_IDLE 1
 }
 
$sequence work {
	a_work
	addlayer progress
	loop
	activity ACT_WORK 1
 }

 
$sequence deployed {
	a_deployed
	activity ACT_CONSTRUCTION 1
 }

$shadowlod 
{
	replacemodel "pg_armory" "pg_armory_slod"
}  

$collisionmodel  "pg_armory_phy.smd"
{
$Mass 650
$concave
} 