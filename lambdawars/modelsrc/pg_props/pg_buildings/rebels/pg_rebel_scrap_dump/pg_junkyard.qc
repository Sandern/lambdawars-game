$scale 2.0
$modelname PG_props/pg_buildings/rebels/pg_junkyard.mdl
$cdmaterials "models/PG_props/pg_buildings/rebels" "models/PG_props/pg_buildings/" 

$body pg_junkyard "pg_junkyard.smd"


//__LOD__
$lod 100
{
      replacemodel "pg_junkyard.smd" "pg_junkyard_low.smd"
}

$weightlist progress_weight {
	"root" 0
	"scrap" 0
	"counter" 0
	"hut_exit" 0
	"chimney" 0
	"number1" 1.0
	"number2" 1.0
	"number3" 1.0
}

$surfaceprop wood
$eyeposition 0 0 35

$attachment "root" "root" 0.00 0.00 0.00 rotate 0 0 0
$attachment "chimney" "chimney" 0.00 0.00 0.00 rotate 0 0 0
$attachment "hut_exit" "hut_exit" 0.00 0.00 0.00 rotate 0 0 0

$animation a_idle "idle"   
$animation a_deployed "construction" 
$animation a_work "work" 
$animation a_zero "zero" 


$animation a_scrap_up "idle" subtract a_idle 0 noanimation
$animation a_scrap_down "idle_scrap_down" subtract a_idle 0 

$animation a_pA0 "p_A" frames 0 0 subtract a_zero 0 noanimation
$animation a_pA1 "p_A" frames 1 1 subtract a_zero 0 
$animation a_pA2 "p_A" frames 2 2 subtract a_zero 0 
$animation a_pA3 "p_A" frames 3 3 subtract a_zero 0 
$animation a_pA4 "p_A" frames 4 4 subtract a_zero 0 
$animation a_pA5 "p_A" frames 5 5 subtract a_zero 0 
$animation a_pA6 "p_A" frames 6 6 subtract a_zero 0 
$animation a_pA7 "p_A" frames 7 7 subtract a_zero 0 
$animation a_pA8 "p_A" frames 8 8 subtract a_zero 0 
$animation a_pA9 "p_A" frames 9 9 subtract a_zero 0 
$animation a_pA10 "p_A" frames 10 10 subtract a_zero 0 

$animation a_pB0 "p_B" frames 0 0 subtract a_zero 0 noanimation
$animation a_pB1 "p_B" frames 1 1 subtract a_zero 0 
$animation a_pB2 "p_B" frames 2 2 subtract a_zero 0 
$animation a_pB3 "p_B" frames 3 3 subtract a_zero 0 
$animation a_pB4 "p_B" frames 4 4 subtract a_zero 0 
$animation a_pB5 "p_B" frames 5 5 subtract a_zero 0 
$animation a_pB6 "p_B" frames 6 6 subtract a_zero 0 
$animation a_pB7 "p_B" frames 7 7 subtract a_zero 0 
$animation a_pB8 "p_B" frames 8 8 subtract a_zero 0 
$animation a_pB9 "p_B" frames 9 9 subtract a_zero 0 
$animation a_pB10 "p_B" frames 10 10 subtract a_zero 0 

$animation a_pC0 "p_C" frames 0 0 subtract a_zero 0 noanimation
$animation a_pC1 "p_C" frames 1 1 subtract a_zero 0 
$animation a_pC2 "p_C" frames 2 2 subtract a_zero 0 
$animation a_pC3 "p_C" frames 3 3 subtract a_zero 0 
$animation a_pC4 "p_C" frames 4 4 subtract a_zero 0 
$animation a_pC5 "p_C" frames 5 5 subtract a_zero 0 
$animation a_pC6 "p_C" frames 6 6 subtract a_zero 0 
$animation a_pC7 "p_C" frames 7 7 subtract a_zero 0 
$animation a_pC8 "p_C" frames 8 8 subtract a_zero 0 
$animation a_pC9 "p_C" frames 9 9 subtract a_zero 0 
$animation a_pC10 "p_C" frames 10 10 subtract a_zero 0 

 //-- ANIMATION --
 $sequence progressA {
	a_pA0 a_pA1 a_pA2 a_pA3 a_pA4 a_pA5 a_pA6 a_pA7 a_pA8 a_pA9 a_pA10
	blendwidth 11
	blend progressA 0 10
	//weightlist progress_weight
	delta
	hidden
 }
 $sequence progressB {
	a_pB0 a_pB1 a_pB2 a_pB3 a_pB4 a_pB5 a_pB6 a_pB7 a_pB8 a_pB9 a_pB10
	blendwidth 11
	blend progressB 0 10
	//weightlist progress_weight
	delta
	hidden
 }
 
 $sequence progressC {
	a_pC0 a_pC1 a_pC2 a_pC3 a_pC4 a_pC5 a_pC6 a_pC7 a_pC8 a_pC9 a_pC10
	blendwidth 11
	blend progressC 0 10
	//weightlist progress_weight
	delta
	hidden
 }
 
 
$sequence scrap_down {
	a_scrap_up a_scrap_down
	blendwidth 2
	blend scrap 0 100
	delta
	hidden
 }
 
$sequence idle {
	a_idle
	addlayer scrap_down
	loop
	activity ACT_IDLE 1
 }
 
 $sequence work {
	a_work
	fadein 0.0
	fadeout 0.0 
	addlayer scrap_down
	addlayer progressA
	addlayer progressB
	addlayer progressc
	snap
	loop
	activity ACT_WORK 1
 }
 
$sequence deployed {
	a_deployed
	addlayer scrap_down
	activity ACT_CONSTRUCTION 1
 }

$collisionmodel  "pg_junkyard_phy.smd"
{
$Mass 650
$concave
} 