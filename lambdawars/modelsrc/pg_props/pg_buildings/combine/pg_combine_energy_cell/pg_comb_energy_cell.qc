$scale 1.2
$modelname PG_props/pg_buildings/combine/pg_combine_energy_cell.mdl
$cdmaterials "models/PG_props/pg_buildings/combine" 

$body pg_comb_energy_cell "pg_comb_energy_cell.smd"

$surfaceprop	metal
$eyeposition 0 0 75

$attachment "root" "power_cell" 0.00 0.00 0.00 rotate 0 0 0
$attachment "coreMid" "power_m" 0.00 0.00 0.00 rotate 0 0 0
$attachment "coreRight" "power_r" 0.00 0.00 0.00 rotate 0 0 0
$attachment "coreLeft" "power_l" 0.00 0.00 0.00 rotate 0 0 0

$animation a_idle "idle"   
$animation a_deployed "pg_comb_energy_cell_build" 
$animation a_work "work" 
$animation a_s0 "idle" subtract a_idle 0  
$animation a_s1 "work" subtract a_idle 0  
$animation a_p0 "p0" subtract a_idle 0 noanimation 
$animation a_p1 "p1" subtract a_idle 0 
$animation a_p2 "p2" subtract a_idle 0


//-- ANIMATION --

 $sequence progress {
	a_p0 a_p1 a_p2
	blendwidth 3
	blend progress 0 100
	loop
	delta
	hidden
 }

  $sequence shake {
	a_s0 a_s1
	blendwidth 2
	blend progress 0 100
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
	nothing
	addlayer progress
	addlayer shake
	loop
	activity ACT_WORK 1
 }

 
$sequence deployed {
	a_deployed
	activity ACT_CONSTRUCTION 1
 }

$shadowlod 
{
	replacemodel "pg_comb_energy_cell" "pg_comb_energy_cell_slod"
}  

$collisionmodel  "pg_comb_energy_cell_phy.smd"
{
$Mass 650
$concave
} 