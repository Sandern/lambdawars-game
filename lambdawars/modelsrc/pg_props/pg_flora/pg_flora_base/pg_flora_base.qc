$scale 1.0
$modelname PG_props/pg_flora/pg_flora_base.mdl
$cdmaterials models/pg_props/pg_flora

//$contents "solid"
$body pg_grass04 "pg_grass04.smd"

$surfaceprop	wood

$animation a_idle "idle" 

$animation a_y_p "idle_y_p" subtract a_idle 0 loop 
$animation a_y_n "idle_y_n" subtract a_idle 0 loop 

$animation a_x_p "idle_x_p" subtract a_idle 0 loop
$animation a_x_n "idle_x_n" subtract a_idle 0 loop

$animation a_z_up "idle" subtract a_idle 0 loop
$animation a_z_down "idle_down2" subtract a_idle 0 loop

 $sequence swayX {
	a_x_n a_x_p
	blendwidth 2
	blend x -1 1
	delta
	hidden
 }
 
$sequence swayY {
	a_y_n a_y_p
	blendwidth 2
	blend y -1 1
	delta
	hidden
 }

 
$sequence swayZ {
	a_z_up a_z_down
	blendwidth 2
	blend z 0 1
	delta
	hidden
}

//-- ANIMATION --
$sequence idle {
	a_idle
	addlayer swayX
	addlayer swayY
	addlayer swayZ
	loop
	activity ACT_IDLE 1
}

$sequence down "down.smd"
$sequence downidle "down_idle.smd"
$sequence up "up.smd"
$sequence kill "kill.smd"
$sequence regrow "regrow.smd"

$hboxset "default"

//$hbox 0 "root" -32.50    0.00  -32.50    32.50   20.00   32.50

//$hbox 0 "top" 0.00    0.00  0.00    0.00  0.00   0.00
