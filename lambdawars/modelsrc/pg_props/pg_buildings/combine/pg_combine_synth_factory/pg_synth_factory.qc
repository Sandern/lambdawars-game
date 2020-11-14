$scale 1.9
$modelname PG_props/pg_buildings/combine/pg_synth_factory.mdl
$cdmaterials "models/PG_props/pg_buildings/combine" "models/PG_props/pg_obj"

$body pg_synth_factory "pg_synth_factory.smd"

$surfaceprop metal
$eyeposition 0 0 2

$attachment "light_a01" "light_a01" 0.00 0.00 0.00 rotate 0 0 0
$attachment "light_a02" "light_a02" 0.00 0.00 0.00 rotate 0 0 0
$attachment "light_a03" "light_a03" 0.00 0.00 0.00 rotate 0 0 0

$animation a_idle "idle"  
$animation a_deployed "construction" 
$animation a_work "work" 

$animation a_p0 "p0" subtract a_idle 0 noanimation 
$animation a_p1 "p1" subtract a_idle 0 
$animation a_p2 "p2" subtract a_idle 0 
$animation a_p3 "p3" subtract a_idle 0  
$animation a_p4 "p4" subtract a_idle 0  
$animation a_p5 "p5" subtract a_idle 0  
$animation a_p6 "p6" subtract a_idle 0  

$sequence progress {
	a_p0 a_p1 a_p2 a_p3 a_p4 a_p5 a_p6 a_p0
	blendwidth 8
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
	loop
	activity ACT_WORK 1
}

 
$sequence deployed {
	a_deployed
	activity ACT_CONSTRUCTION 1
 }

 $collisionmodel  "pg_synth_factory_phy.smd"
{
$Mass 650
$concave
} 