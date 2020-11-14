$scale 1.9
$modelname pg_props/pg_buildings/other/pg_flagpole/pg_flagpole_wood.mdl
$cdmaterials models/pg_props/pg_buildings/other/pg_flagpole

$body pg_flagpole_wood "pg_flagpole_wood.smd"

$weightlist flag "root" 0.0 "wire01" 1.0 "Bone001" 1.0  "Bone002" 1.0 "Bone003" 1.0  "Bone004" 1.0 "Bone005" 1.0  "Bone006" 1.0 "Bone007" 1.0  "Bone008" 1.0 "Bone009" 1.0  "Bone010" 1.0 "Bone011" 1.0  "Bone012" 1.0


$surfaceprop	wood

$animation a_idle "pg_flagpole_wood_idle"  loop 
$animation a_idle_down "pg_flagpole_wood_idle_down"  loop 

$animation a_deployed_down "pg_flagpole_rebels_build" 
$animation a_deployed_up "pg_flagpole_rebels_build_up" 

$sequence deployed {
a_deployed_up
a_deployed_down
blendwidth 2 

blend flag 100 0
activity ACT_CONSTRUCTION 1
}
 
$sequence idle {
a_idle 
a_idle_down
blendwidth 2 

blend flag 100 0
activity ACT_IDLE 1
}

//__skinfamilies__
$texturegroup skinfamilies
{
	{ "pg_wars_flag"   }
	{ "pg_wars_flag_skin2"   }
	{ "pg_wars_flag_skin3"   }

}




$collisionmodel "pg_flagpole_wood_phy.smd"
{
$Mass 150
$concave
} 