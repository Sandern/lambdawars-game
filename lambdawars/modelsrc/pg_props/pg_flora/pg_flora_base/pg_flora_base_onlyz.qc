$scale 1.0
$modelname PG_props/pg_flora/pg_flora_base_onlyz.mdl
$cdmaterials models/pg_props/pg_flora

//$contents "solid"
$body pg_grass04 "pg_grass04.smd"

$surfaceprop	wood

$animation a_idle "idle" 

$animation a_z_up "idle" subtract a_idle 0 loop 
$animation a_z_down "idle_down2" subtract a_idle 0 loop 

 
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
