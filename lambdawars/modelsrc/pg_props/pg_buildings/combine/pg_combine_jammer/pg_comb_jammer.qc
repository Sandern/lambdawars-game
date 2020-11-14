// The original idear was that this building would disturb enemys field of view
// But now it is used as a the combine regeneration outpost
$scale 2.0
$modelname PG_props/pg_buildings/combine/pg_combine_jammer.mdl
$cdmaterials "models/PG_props/pg_buildings/combine" 

$body pg_comb_jammer "pg_comb_jammer.smd"

$surfaceprop metal
$eyeposition 0 0 45

$attachment "root" "root" 0.00 0.00 0.00 rotate 0 0 0
$attachment "light" "light" 0.00 0.00 0.00 rotate 0 0 0

$attachment "p0" "p0" 0.00 0.00 0.00 rotate 0 0 0
$attachment "p1" "p1" 0.00 0.00 0.00 rotate 0 0 0
$attachment "p2" "p2" 0.00 0.00 0.00 rotate 0 0 0

$animation a_idle "pg_comb_jammer_idle"   
$animation a_work "pg_comb_jammer_work"   
$animation a_deployed "pg_comb_jammer_construction" 
$animation a_regdoll "pg_comb_jammer_regdoll" 

$animation a_p0 "pg_comb_jammer_regdoll" subtract a_regdoll 0 noanimation 
$animation a_p1 "pg_comb_jammer_up" subtract a_regdoll 0  
$animation a_p2 "pg_comb_jammer_down" subtract a_regdoll 0 



//-- ANIMATION --
$sequence progress {
	a_p0 a_p1 a_p2 a_p0
	blendwidth 4
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

$collisionmodel  "pg_comb_jammer_phy.smd"
{
$Mass 650
$concave
} 