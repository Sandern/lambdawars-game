$scale 1.8
$modelname PG_props/pg_buildings/combine/pg_combine_hq.mdl
$cdmaterials "models/PG_props/pg_buildings/combine" 

$body pg_combine_hq "pg_combine_hq.smd"

$surfaceprop metal
$eyeposition 0 0 75

$attachment "root" "root" 0.00 0.00 0.00 rotate 0 0 0
$attachment "light" "light" 0.00 0.00 0.00 rotate 0 0 0
$attachment "top" "top" 0.00 0.00 0.00 rotate 0 0 0

$animation a_idle "idle"   
$animation a_deployed "construction" 
$animation a_work "work" 

$animation a_p0 "p0" subtract a_idle 0 noanimation 
$animation a_p1 "p1" subtract a_idle 0 
$animation a_p2 "p2" subtract a_idle 0 
$animation a_p3 "p3" subtract a_idle 0  


//-- ANIMATION --
$sequence progress {
	a_p0 a_p1 a_p2 a_p3 a_p0
	blendwidth 5
	blend progress 0 100
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
	fadein 0.0
	fadeout 0.0 
	snap
	loop
	activity ACT_WORK 1
 }

 
$sequence deployed {
	a_deployed
	activity ACT_CONSTRUCTION 1
 }

$shadowlod 
{
	replacemodel "pg_combine_hq" "pg_combine_hq_slod"
}  

$collisionmodel  "pg_combine_hq_phy.smd"
{
$Mass 650
$concave
} 