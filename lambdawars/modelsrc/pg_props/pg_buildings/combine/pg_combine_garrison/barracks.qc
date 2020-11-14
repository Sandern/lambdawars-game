$ModelName "structures\combine\barracks.mdl"
$CDMaterials "models\structures\combine\"

$Scale 0.50

$StaticProp

$BodyGroup "Body"
{
	studio "barracks.smd"
}

$SurfaceProp "metal"

$Contents "solid"

$MaxEyeDeflection 90

$CBox 0 0 0 0 0 0


$Sequence "idle" {
	"barracks_anims\idle.smd"
	fadein 0.2
	fadeout 0.2
	fps 30
}

$CollisionModel "barracks_physics.smd"
{
	$mass 500
	$inertia 1
	$damping 0
	$rotdamping 0
	$rootbone " "
	$concave
}
