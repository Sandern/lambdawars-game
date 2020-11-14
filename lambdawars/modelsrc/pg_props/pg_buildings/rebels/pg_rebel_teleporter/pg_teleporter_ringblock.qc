$scale 1.5
$modelname PG_props/pg_buildings/rebels/pg_teleporter_ringblock.mdl
$cdmaterials "models/pg_props/pg_cinematic/" 

$body pg_teleporter_block "pg_teleporter_ringblock.smd"

$sequence idle {
	pg_teleporter_ringblock
	loop
	activity ACT_IDLE 1
 }
 
$collisionmodel  "pg_teleporter_ringblock_phy.smd"
{
$Mass 650
$concave
} 