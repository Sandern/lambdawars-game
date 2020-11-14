$scale 0.725
$modelname "wars_structures\combine\comb_mech.mdl"
$cdmaterials "models\wars_structures\combine"

$body comb_mech "comb_mech.smd"
$bodygroup construction
{
	studio "comb_mech_m2.smd"
	blank
}


$surfaceprop metal
$attachment "root" "root" 0.00 0.00 0.00 rotate 90 0 0


 //-- ANIMATION --
$animation a_idle "comb_mech_idle"  
$animation a_work "comb_mech_work"  
$animation a_deployed "comb_mech_construction"  


$animation a_p0 "comb_mech_idle" subtract a_idle 0 noanimation
$animation a_p1 "comb_mech_p1" subtract a_idle 0 
$animation a_p2 "comb_mech_p2" subtract a_idle 0 
$animation a_p3 "comb_mech_p3" subtract a_idle 0 

$sequence progress {
	a_p0 a_p1 a_p2 a_p3 a_p0
	blendwidth 5
	blend progress 0 100
	fps 30 loop
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

$collisionmodel  "comb_mech_phys.smd"
{
$Mass 650
$concave
} 