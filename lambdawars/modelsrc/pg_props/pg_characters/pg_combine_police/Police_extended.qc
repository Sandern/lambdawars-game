// Created by Crowbar 0.24.0.0

$modelname "Police_extended.mdl"

$model "police" "Police_reference.smd" 

$bodygroup "manhack"
{
	blank
	studio "Police_manhack_reference.smd"
}

$lod 12
{
	replacemodel "Police_reference.smd" "Police_police_reference_lod1.smd"
	replacemodel "Police_manhack_reference.smd" "Police_manhack_reference_lod1.smd"
}
$lod 18
{
	replacemodel "Police_reference.smd" "Police_police_reference_lod2.smd"
	replacemodel "Police_manhack_reference.smd" "Police_manhack_reference_lod2.smd"
}
$lod 42
{
	replacemodel "Police_reference.smd" "Police_police_reference_lod3.smd"
	replacemodel "Police_manhack_reference.smd" "Police_manhack_reference_lod3.smd"
}
$lod 55
{
	replacemodel "Police_reference.smd" "Police_police_reference_lod4.smd"
	replacemodel "Police_manhack_reference.smd" "Police_manhack_reference_lod4.smd"
}
$lod 80
{
	replacemodel "Police_reference.smd" "Police_police_reference_lod5.smd"
	replacemodel "Police_manhack_reference.smd" "Police_manhack_reference_lod5.smd"
}
$shadowlod
{
	replacemodel "Police_reference.smd" "Police_police_reference_lod6.smd"
	replacemodel "Police_manhack_reference.smd" "Police_manhack_reference_lod6.smd"
}

$cdmaterials "models\Police\"
$cdmaterials "models\manhack\"

$attachment "eyes" "ValveBiped.Bip01_Head1" 3.34 -5.28 0 rotate 0 -80.1 -90
$attachment "Center" "ValveBiped.Bip01_Spine1" -6.2 2.09 0 rotate 0 96.62 90
$attachment "Chest" "ValveBiped.Bip01_Spine4" -2.7 3.88 0 rotate 0 79.75 90
$attachment "LHand" "ValveBiped.Bip01_L_Hand" 3 0 0 rotate 0 0 0
$attachment "RHand" "ValveBiped.Bip01_R_Hand" 3 0 0 rotate 0 0 0
$attachment "zipline" "ValveBiped.Bip01_Spine4" 2 -2 0 rotate 0 -17 0
$attachment "manhack" "ValveBiped.Bip01_Spine" 18 -6 3 rotate -25 50 0
$attachment "forward" "ValveBiped.forward" 0 0 0 rotate 0 0 0
$attachment "anim_attachment_RH" "ValveBiped.Anim_Attachment_RH" 0 0 0 rotate -90 -90 0
$attachment "anim_attachment_LH" "ValveBiped.Anim_Attachment_LH" 0 0 0 rotate -90 -90 0
$attachment "anim_attachment_head" "ValveBiped.Bip01_Head1" 0 0 0 rotate -90 -90 0

$surfaceprop "flesh"

$jointsurfaceprop "ValveBiped.Bip01_Head1" "no_decal"
$jointsurfaceprop "ValveBiped.forward" "no_decal"

$contents "solid"

$eyeposition 0 0 72

// $hboxset "default"
// $hbox 1 "ValveBiped.Bip01_Head1" -3.5 -7.71 -3.85 7.5 5.71 3.96
// $hbox 4 "ValveBiped.Bip01_L_UpperArm" 0 -3.37 -3.7 12.51 3.4 2.41
// $hbox 4 "ValveBiped.Bip01_L_Forearm" -0.9 -3.49 -3.17 9.49 3.1 2.41
// $hbox 4 "ValveBiped.Bip01_L_Hand" -1.11 -1.89 -2.38 5.72 1.46 2.34
// $hbox 5 "ValveBiped.Bip01_R_UpperArm" 0 -3.37 -2.37 12.39 3.41 3.8
// $hbox 5 "ValveBiped.Bip01_R_Forearm" -0.99 -3.5 -2.37 9.33 3.1 3.27
// $hbox 5 "ValveBiped.Bip01_R_Hand" -1.19 -1.86 -2.33 5.31 1.94 2.61
// $hbox 6 "ValveBiped.Bip01_L_Thigh" 0 -6 -3.55 17.85 4 4.45
// $hbox 6 "ValveBiped.Bip01_L_Calf" 0 -3.51 -3.28 15.64 3.49 2.72
// $hbox 6 "ValveBiped.Bip01_L_Foot" -1.07 -2 -2.84 5.04 5 2.16
// $hbox 6 "ValveBiped.Bip01_L_Toe0" -0.5 -3 -2.19 2.5 0 2.46
// $hbox 7 "ValveBiped.Bip01_R_Thigh" 0 -6 -4.55 17.85 4 3.4
// $hbox 7 "ValveBiped.Bip01_R_Calf" 0 -3.51 -2.82 15.64 3.49 3.18
// $hbox 7 "ValveBiped.Bip01_R_Foot" -1.06 -2.01 -2.28 5.05 4.99 2.72
// $hbox 7 "ValveBiped.Bip01_R_Toe0" -0.5 -3 -2.6 2.5 0 2.1
// $hbox 3 "ValveBiped.Bip01_Pelvis" -7.5 -6 -6 7.5 6 6
// $hbox 2 "ValveBiped.Bip01_Spine2" -6.5 -2.5 -7 10.5 7.5 7

// NOTE: The following commented-out $definebone lines might be needed, as is often the case for view models. When needed, simply remove the two slashes '//' from the start of each line.
// $definebone "ValveBiped.Bip01_Pelvis" "" -0.000005 -0.533615 38.566917 1.570796 0 0 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_Spine" "ValveBiped.Bip01_Pelvis" 0.000005 3.345128 -2.981901 1.570796 0.086293 1.570796 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_Spine1" "ValveBiped.Bip01_Spine" 4.018331 0 0 0 0 -0.029242 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_Spine2" "ValveBiped.Bip01_Spine1" 3.518568 0 0 0 0 0.100336 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_Spine4" "ValveBiped.Bip01_Spine2" 8.942642 0 0 0 0 0.194096 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_Neck1" "ValveBiped.Bip01_Spine4" 3.307271 0 0 3.14159 0 0.400478 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_Head1" "ValveBiped.Bip01_Neck1" 3.593712 -0.000002 0 0 -0.000001 0.406587 0 0 0 0 0 0
// $definebone "ValveBiped.forward" "ValveBiped.Bip01_Head1" 1.999998 -3.000001 0 -1.570796 0 -1.32645 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Clavicle" "ValveBiped.Bip01_Spine4" 2.033353 1.000771 -1.93761 -1.668474 1.286518 2.942953 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_UpperArm" "ValveBiped.Bip01_R_Clavicle" 6.028142 0.000005 0 1.639479 -0.008065 -0.586846 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Forearm" "ValveBiped.Bip01_R_UpperArm" 11.692548 0 0 0 0 -0.060372 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Hand" "ValveBiped.Bip01_R_Forearm" 11.481695 0 0.000003 -1.564937 0.106606 0.044193 0 0 0 0 0 0
// $definebone "ValveBiped.Anim_Attachment_RH" "ValveBiped.Bip01_R_Hand" 2.676085 -1.712441 0 -1.570796 0 -1.570796 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Clavicle" "ValveBiped.Bip01_Spine4" 2.033346 1.000767 1.93766 1.596637 -1.286515 2.942961 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_UpperArm" "ValveBiped.Bip01_L_Clavicle" 6.028142 0.000001 0 -1.579613 0.047802 -0.585173 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Forearm" "ValveBiped.Bip01_L_UpperArm" 11.692556 0 0.000003 0 0 -0.060372 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Hand" "ValveBiped.Bip01_L_Forearm" 11.481669 0 -0.000027 1.573183 -0.106613 0.044193 0 0 0 0 0 0
// $definebone "ValveBiped.Anim_Attachment_LH" "ValveBiped.Bip01_L_Hand" 2.676088 -1.712441 0 1.570797 0 1.570796 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Thigh" "ValveBiped.Bip01_Pelvis" -3.890452 0.000004 0.000007 -1.570796 0.051845 -1.576021 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Calf" "ValveBiped.Bip01_R_Thigh" 17.848171 0 0 0 0 0.034187 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Foot" "ValveBiped.Bip01_R_Calf" 16.525253 0 0 0.038611 0.040779 -1.071632 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Toe0" "ValveBiped.Bip01_R_Foot" 6.879453 0 0 -0.081333 -0.002951 -0.584373 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Thigh" "ValveBiped.Bip01_Pelvis" 3.890452 -0.000004 -0.000003 -1.570796 0.051839 -1.565574 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Calf" "ValveBiped.Bip01_L_Thigh" 17.848175 0 0 0 0 0.0342 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Foot" "ValveBiped.Bip01_L_Calf" 16.525248 0 0 -0.027915 -0.040782 -1.071638 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Toe0" "ValveBiped.Bip01_L_Foot" 6.879448 -0.000001 0.000001 -0.007299 -0.002951 -0.584373 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger4" "ValveBiped.Bip01_L_Hand" 3.859705 -0.142404 -1.191976 -0.479144 0.15219 -0.879874 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger41" "ValveBiped.Bip01_L_Finger4" 1.31256 0.000001 0.000001 0 0.009665 -0.43972 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger42" "ValveBiped.Bip01_L_Finger41" 0.729363 0.000003 0 0 0.004971 -0.244299 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger3" "ValveBiped.Bip01_L_Hand" 3.942326 0.046772 -0.431443 -0.155014 0.073328 -0.810648 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger31" "ValveBiped.Bip01_L_Finger3" 1.539091 0.000003 0 0 0.00446 -0.247797 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger32" "ValveBiped.Bip01_L_Finger31" 1.196321 -0.000002 0 0 0.007361 -0.430802 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger2" "ValveBiped.Bip01_L_Hand" 3.88369 -0.046771 0.431443 0.085902 0.02183 -0.587867 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger21" "ValveBiped.Bip01_L_Finger2" 1.719576 0.000001 0 0 0.005516 -0.366478 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger22" "ValveBiped.Bip01_L_Finger21" 1.209181 0 0 0 0.003084 -0.2164 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger1" "ValveBiped.Bip01_L_Hand" 3.859859 -0.137948 1.332467 0.354449 -0.04275 -0.531718 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger11" "ValveBiped.Bip01_L_Finger1" 1.719428 0.000002 0 0 0.004074 -0.363009 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger12" "ValveBiped.Bip01_L_Finger11" 1.099667 0.000001 0 0 0.002596 -0.244331 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger0" "ValveBiped.Bip01_L_Hand" 0.806048 -0.348922 1.321259 -1.206854 -0.679489 -0.789308 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger01" "ValveBiped.Bip01_L_Finger0" 1.789784 -0.000001 0.000001 0 0.007386 0.228523 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger02" "ValveBiped.Bip01_L_Finger01" 1.206999 0 0.000002 0 0.011266 0.36286 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger4" "ValveBiped.Bip01_R_Hand" 3.859671 -0.132567 1.193107 0.47914 -0.158545 -0.879041 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger41" "ValveBiped.Bip01_R_Finger4" 1.31256 0 -0.000001 0 -0.011932 -0.439672 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger42" "ValveBiped.Bip01_R_Finger41" 0.729362 0.000002 0 0 -0.006134 -0.244271 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger3" "ValveBiped.Bip01_R_Hand" 3.94229 0.050333 0.431043 0.154999 -0.079305 -0.810205 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger31" "ValveBiped.Bip01_R_Finger3" 1.539096 0.000002 0 0 -0.005854 -0.247771 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger32" "ValveBiped.Bip01_R_Finger31" 1.196325 0 0 0 -0.009663 -0.430761 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger2" "ValveBiped.Bip01_R_Hand" 3.883654 -0.050327 -0.431043 -0.085905 -0.026404 -0.587695 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger21" "ValveBiped.Bip01_R_Finger2" 1.719576 0.000003 0 0 -0.007974 -0.366436 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger22" "ValveBiped.Bip01_R_Finger21" 1.20918 -0.000002 0 0 -0.004461 -0.216376 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger1" "ValveBiped.Bip01_R_Hand" 3.859828 -0.148937 -1.331281 -0.354419 0.038567 -0.532001 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger11" "ValveBiped.Bip01_R_Finger1" 1.719426 -0.000001 0 0 -0.006613 -0.36297 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger12" "ValveBiped.Bip01_R_Finger11" 1.099664 0.000001 0 0 -0.004211 -0.244313 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger0" "ValveBiped.Bip01_R_Hand" 0.806015 -0.359835 -1.318333 1.2042 0.673618 -0.793956 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger01" "ValveBiped.Bip01_R_Finger0" 1.789783 0 0.000002 0 -0.006301 0.228555 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger02" "ValveBiped.Bip01_R_Finger01" 1.207 0 0.000001 0 -0.009618 0.362905 0 0 0 0 0 0
// $definebone "ValveBiped.baton_parent" "ValveBiped.Bip01_R_Hand" 2.338452 -1.53574 -6.391508 1.520245 -0.09438 -2.001951 0 0 0 0 0 0




$sequence "ragdoll" "Police_anims\ragdoll.smd" {
	fps 30
	activity "ACT_DIERAGDOLL" 1
}

$includemodel "Police_animations.mdl"
$includemodel "Police_animations_extra.mdl"
$includemodel "Police_ss.mdl"

$ikchain "rhand" "ValveBiped.Bip01_R_Hand" knee 0.707 0.707 0
$ikchain "lhand" "ValveBiped.Bip01_L_Hand" knee 0.707 0.707 0
$ikchain "rfoot" "ValveBiped.Bip01_R_Foot" knee 0.707 -0.707 0
$ikchain "lfoot" "ValveBiped.Bip01_L_Foot" knee 0.707 -0.707 0

$ikautoplaylock "rfoot" 1 0.1
$ikautoplaylock "lfoot" 1 0.1

$collisionjoints "Police_physics.smd"
{
	$mass 0
	$inertia 2
	$damping 0.01
	$rotdamping 0.4


	$jointconstrain "ValveBiped.Bip01_Spine2" x limit -48 48 0.2
	$jointconstrain "ValveBiped.Bip01_Spine2" y limit -25 25 0.2
	$jointconstrain "ValveBiped.Bip01_Spine2" z limit -25 50 0.2

	$jointconstrain "ValveBiped.Bip01_R_UpperArm" x limit -50 57 0.2
	$jointconstrain "ValveBiped.Bip01_R_UpperArm" y limit -19 102 0.2
	$jointconstrain "ValveBiped.Bip01_R_UpperArm" z limit -93 30 0.2

	$jointconstrain "ValveBiped.Bip01_L_UpperArm" x limit -50 57 0.2
	$jointconstrain "ValveBiped.Bip01_L_UpperArm" y limit -102 19 0.2
	$jointconstrain "ValveBiped.Bip01_L_UpperArm" z limit -93 30 0.2

	$jointmassbias "ValveBiped.Bip01_L_Forearm" 2
	$jointconstrain "ValveBiped.Bip01_L_Forearm" x limit 0 0 0
	$jointconstrain "ValveBiped.Bip01_L_Forearm" y limit 0 0 0
	$jointconstrain "ValveBiped.Bip01_L_Forearm" z limit -120 4 0.2

	$jointmassbias "ValveBiped.Bip01_L_Hand" 4
	$jointconstrain "ValveBiped.Bip01_L_Hand" x limit -60 60 0.2
	$jointconstrain "ValveBiped.Bip01_L_Hand" y limit -30 30 0.2
	$jointconstrain "ValveBiped.Bip01_L_Hand" z limit -57 70 0.2

	$jointmassbias "ValveBiped.Bip01_R_Forearm" 2
	$jointconstrain "ValveBiped.Bip01_R_Forearm" x limit 0 0 0.2
	$jointconstrain "ValveBiped.Bip01_R_Forearm" y limit 0 0 0.2
	$jointconstrain "ValveBiped.Bip01_R_Forearm" z limit -120 4 0.2

	$jointmassbias "ValveBiped.Bip01_R_Hand" 4
	$jointconstrain "ValveBiped.Bip01_R_Hand" x limit -60 60 0.2
	$jointconstrain "ValveBiped.Bip01_R_Hand" y limit -30 30 0.2
	$jointconstrain "ValveBiped.Bip01_R_Hand" z limit -57 70 0.2

	$jointconstrain "ValveBiped.Bip01_R_Thigh" x limit -25 39 0.2
	$jointconstrain "ValveBiped.Bip01_R_Thigh" y limit -8 75 0.2
	$jointconstrain "ValveBiped.Bip01_R_Thigh" z limit -97 32 0.2

	$jointmassbias "ValveBiped.Bip01_R_Calf" 2
	$jointconstrain "ValveBiped.Bip01_R_Calf" x limit 0 0 0.2
	$jointconstrain "ValveBiped.Bip01_R_Calf" y limit 0 0 0.2
	$jointconstrain "ValveBiped.Bip01_R_Calf" z limit -12 126 0.2

	$jointmassbias "ValveBiped.Bip01_Head1" 2
	$jointconstrain "ValveBiped.Bip01_Head1" x limit -20 20 0.2
	$jointconstrain "ValveBiped.Bip01_Head1" y limit -25 25 0.2
	$jointconstrain "ValveBiped.Bip01_Head1" z limit -13 30 0.2

	$jointconstrain "ValveBiped.Bip01_L_Thigh" x limit -25 20 0.2
	$jointconstrain "ValveBiped.Bip01_L_Thigh" y limit -73 6 0.2
	$jointconstrain "ValveBiped.Bip01_L_Thigh" z limit -93 30 0.2

	$jointmassbias "ValveBiped.Bip01_L_Calf" 2
	$jointconstrain "ValveBiped.Bip01_L_Calf" x limit 0 0 0.2
	$jointconstrain "ValveBiped.Bip01_L_Calf" y limit 0 0 0.2
	$jointconstrain "ValveBiped.Bip01_L_Calf" z limit -8 126 0.2

	$jointmassbias "ValveBiped.Bip01_L_Foot" 2
	$jointconstrain "ValveBiped.Bip01_L_Foot" x limit -1 -1 0.2
	$jointconstrain "ValveBiped.Bip01_L_Foot" y limit -19 19 0.2
	$jointconstrain "ValveBiped.Bip01_L_Foot" z limit -15 35 0.2

	$jointmassbias "ValveBiped.Bip01_R_Foot" 2
	$jointconstrain "ValveBiped.Bip01_R_Foot" x limit 0 0 0
	$jointconstrain "ValveBiped.Bip01_R_Foot" y limit -21 6 0.2
	$jointconstrain "ValveBiped.Bip01_R_Foot" z limit -15 35 0.2
}

$collisiontext
{
	animatedfriction 
	{
		"animfrictionmin" "1.000000"
		"animfrictionmax" "1000.000000"
		"animfrictiontimein" "0.800000"
		"animfrictiontimeout" "0.500000"
		"animfrictiontimehold" "0.000000"
	}
	editparams 
	{
		"rootname" "valvebiped.bip01_pelvis"
		"totalmass" "90.000000"
		"jointmerge" "valvebiped.bip01_pelvis,valvebiped.bip01"
		"jointmerge" "valvebiped.bip01_pelvis,valvebiped.bip01_spine1"
	}
}

$bonemerge "ValveBiped.Bip01_Pelvis"
$bonemerge "ValveBiped.Bip01_Spine"
$bonemerge "ValveBiped.Bip01_Spine1"
$bonemerge "ValveBiped.Bip01_Spine2"
$bonemerge "ValveBiped.Bip01_Spine4"
$bonemerge "ValveBiped.Bip01_R_Clavicle"
$bonemerge "ValveBiped.Bip01_R_UpperArm"
$bonemerge "ValveBiped.Bip01_R_Forearm"
$bonemerge "ValveBiped.Bip01_R_Hand"
$bonemerge "ValveBiped.Anim_Attachment_RH"
$bonemerge "ValveBiped.baton_parent"

