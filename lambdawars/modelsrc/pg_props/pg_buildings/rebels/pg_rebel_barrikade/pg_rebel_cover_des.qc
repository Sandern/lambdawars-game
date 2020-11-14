$scale 1.9
$modelname PG_props/pg_buildings/rebels/pg_rebel_barricade_des.mdl
$cdmaterials "models/PG_props/pg_buildings" "models/PG_props/pg_obj/pg_flagpole" 

$body pg_rebel_barrikade "pg_rebel_cover_ex.smd"

$surfaceprop	wood

$animation a_destruction01 "pg_rebel_cover_ex_ani"  

 
$sequence destruction01 {
a_destruction01
activity ACT_EXPLODE 1
 }
 