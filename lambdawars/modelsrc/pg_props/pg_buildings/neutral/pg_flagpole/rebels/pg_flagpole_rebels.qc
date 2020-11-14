$scale 1.9
$modelname pg_props/pg_buildings/other/pg_flagpole/pg_flagpole_rebels.mdl
$cdmaterials models/pg_props/pg_buildings/other/pg_flagpole

$body pg_flagpole_rebels "pg_flagpole_rebels.smd"

$weightlist flag "root" 0.0 "wire01" 1.0 "Bone001" 1.0  "Bone002" 1.0 "Bone003" 1.0  "Bone004" 1.0 "Bone005" 1.0  "Bone006" 1.0 "Bone007" 1.0  "Bone008" 1.0 "Bone009" 1.0  "Bone010" 1.0 "Bone011" 1.0  "Bone012" 1.0


$surfaceprop	metal

$animation a_idle "pg_flagpole_rebels_idle"  loop 
$animation a_idle_down "pg_flagpole_rebels_idle_down"  loop 

$sequence idle {
a_idle 
a_idle_down
blendwidth 2 

 blend flag 100 0
 }

//__skinfamilies__
$texturegroup skinfamilies
{
	{ "pg_wars_flag"   }
	{ "pg_wars_flag_skin2"   }
	{ "pg_wars_flag_skin3"   }

}




$collisionmodel "pg_flagpole_rebels_phy.smd"
{
$Mass 150
$concave
} 