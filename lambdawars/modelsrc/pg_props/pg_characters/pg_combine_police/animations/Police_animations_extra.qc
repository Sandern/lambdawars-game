$modelname "Police_animations_extra.mdl"

$poseparameter "body_yaw" -29.73426 29.73423 0
$poseparameter "spine_yaw" -30.7085 30.70848 0
$poseparameter "neck_trans" -0.207508 0.2594 0
$poseparameter "head_yaw" -66.70654 66.70631 0
$poseparameter "head_pitch" -34.86658 25.37666 0
$poseparameter "head_roll" -10.93143 10.85243 0
$poseparameter "move_yaw" -180 180 360
$poseparameter "aim_pitch" -86.32401 56.20353 0
$poseparameter "aim_yaw" -60 60 0

$cdmaterials "models\police_xsi\"

$attachment "forward" "ValveBiped.forward" 0 0 0 rotate 0 0 0
$attachment "anim_attachment_RH" "ValveBiped.Anim_Attachment_RH" 0 0 0 rotate -90 -90 0
$attachment "anim_attachment_LH" "ValveBiped.Anim_Attachment_LH" 0 0 0 rotate -90 -90 0
$attachment "anim_attachment_head" "ValveBiped.Bip01_Head1" 0 0 0 rotate -90 -90 0
$attachment "eyes" "ValveBiped.Bip01_Head1" 2.7 -7.43 0 rotate 0 -80.1 -90
$attachment "baton" "ValveBiped.baton_parent" 0 0 0 rotate 0 0 0

$surfaceprop "default"

$contents "solid"

$definebone "ValveBiped.Bip01_Pelvis" "" -0.000005 -0.533615 38.566917 1.570796 0 0 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_Spine" "ValveBiped.Bip01_Pelvis" 0.000005 3.345128 -2.981901 1.570796 0.086293 1.570796 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_Spine1" "ValveBiped.Bip01_Spine" 4.018331 0 0 0 0 -0.029242 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_Spine2" "ValveBiped.Bip01_Spine1" 3.518565 0 0 0 0 0.100336 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_Spine4" "ValveBiped.Bip01_Spine2" 8.942642 0 0 0 0 0.194096 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_Neck1" "ValveBiped.Bip01_Spine4" 3.307271 0 0 3.14159 0 0.400478 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_Head1" "ValveBiped.Bip01_Neck1" 3.593712 -0.000001 0 0 -0.000001 0.406587 0 0 0 0 0 0
$definebone "ValveBiped.forward" "ValveBiped.Bip01_Head1" 1.999997 -3.000001 0 -1.570796 0 -1.32645 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Clavicle" "ValveBiped.Bip01_Spine4" 2.03335 1.000771 -1.93761 -1.668474 1.286518 2.942953 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_UpperArm" "ValveBiped.Bip01_R_Clavicle" 6.028143 0.000002 0 1.639479 -0.008065 -0.586846 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Forearm" "ValveBiped.Bip01_R_UpperArm" 11.692549 0 0.000002 0 0 -0.060372 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Hand" "ValveBiped.Bip01_R_Forearm" 11.481698 0 0 -1.564937 0.106606 0.044193 0 0 0 0 0 0
$definebone "ValveBiped.Anim_Attachment_RH" "ValveBiped.Bip01_R_Hand" 2.676087 -1.71244 0 -1.570796 0 -1.570796 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Clavicle" "ValveBiped.Bip01_Spine4" 2.033342 1.000767 1.93766 1.596637 -1.286515 2.942961 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_UpperArm" "ValveBiped.Bip01_L_Clavicle" 6.028142 0.000002 0 -1.579613 0.047801 -0.585173 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Forearm" "ValveBiped.Bip01_L_UpperArm" 11.692555 0 0.000005 0 0 -0.060372 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Hand" "ValveBiped.Bip01_L_Forearm" 11.481671 0 -0.00003 1.573183 -0.106613 0.044193 0 0 0 0 0 0
$definebone "ValveBiped.Anim_Attachment_LH" "ValveBiped.Bip01_L_Hand" 2.676088 -1.712441 0 1.570797 0 1.570797 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Thigh" "ValveBiped.Bip01_Pelvis" -3.890452 0.000004 0.000007 -1.570796 0.051845 -1.576021 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Calf" "ValveBiped.Bip01_R_Thigh" 17.848171 0 0 0 0 0.034187 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Foot" "ValveBiped.Bip01_R_Calf" 16.525253 0 0 0.038611 0.040779 -1.071632 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Toe0" "ValveBiped.Bip01_R_Foot" 6.879454 0 0 -0.081333 -0.002951 -0.584373 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Thigh" "ValveBiped.Bip01_Pelvis" 3.890452 -0.000004 -0.000003 -1.570796 0.051839 -1.565574 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Calf" "ValveBiped.Bip01_L_Thigh" 17.848175 0 0 0 0 0.0342 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Foot" "ValveBiped.Bip01_L_Calf" 16.525249 0 0 -0.027915 -0.040782 -1.071638 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Toe0" "ValveBiped.Bip01_L_Foot" 6.879452 0 0 -0.007299 -0.00295 -0.584374 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Finger4" "ValveBiped.Bip01_L_Hand" 3.859704 -0.142404 -1.191975 -0.479144 0.15219 -0.879874 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Finger41" "ValveBiped.Bip01_L_Finger4" 1.312563 0.000001 0.000001 0 0.009665 -0.43972 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Finger42" "ValveBiped.Bip01_L_Finger41" 0.729362 0.000002 0 0 0.004971 -0.244299 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Finger3" "ValveBiped.Bip01_L_Hand" 3.942327 0.046774 -0.431443 -0.155014 0.073328 -0.810648 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Finger31" "ValveBiped.Bip01_L_Finger3" 1.539092 0.000002 0 0 0.00446 -0.247797 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Finger32" "ValveBiped.Bip01_L_Finger31" 1.196319 -0.000001 0 0 0.007361 -0.430802 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Finger2" "ValveBiped.Bip01_L_Hand" 3.883689 -0.046767 0.431443 0.085902 0.02183 -0.587867 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Finger21" "ValveBiped.Bip01_L_Finger2" 1.719575 0.000002 0 0 0.005516 -0.366478 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Finger22" "ValveBiped.Bip01_L_Finger21" 1.209182 -0.000001 0 0 0.003084 -0.2164 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Finger1" "ValveBiped.Bip01_L_Hand" 3.859859 -0.13795 1.332466 0.354449 -0.04275 -0.531718 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Finger11" "ValveBiped.Bip01_L_Finger1" 1.719429 0.000003 0 0 0.004074 -0.363009 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Finger12" "ValveBiped.Bip01_L_Finger11" 1.099668 0.000001 0 0 0.002596 -0.244331 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Finger0" "ValveBiped.Bip01_L_Hand" 0.806048 -0.348923 1.321258 -1.206854 -0.679488 -0.789308 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Finger01" "ValveBiped.Bip01_L_Finger0" 1.789785 0 0.000002 0 0.007387 0.228523 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_L_Finger02" "ValveBiped.Bip01_L_Finger01" 1.206998 0 0 0 0.011267 0.36286 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Finger4" "ValveBiped.Bip01_R_Hand" 3.859672 -0.132566 1.193108 0.47914 -0.158545 -0.879041 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Finger41" "ValveBiped.Bip01_R_Finger4" 1.31256 0 -0.000001 0 -0.011932 -0.439672 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Finger42" "ValveBiped.Bip01_R_Finger41" 0.729361 0.000002 0 0 -0.006134 -0.244271 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Finger3" "ValveBiped.Bip01_R_Hand" 3.942293 0.05033 0.431043 0.154999 -0.079305 -0.810205 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Finger31" "ValveBiped.Bip01_R_Finger3" 1.539095 0.000003 0 0 -0.005854 -0.247771 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Finger32" "ValveBiped.Bip01_R_Finger31" 1.196323 0 0 0 -0.009663 -0.430761 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Finger2" "ValveBiped.Bip01_R_Hand" 3.883655 -0.050326 -0.431043 -0.085905 -0.026404 -0.587695 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Finger21" "ValveBiped.Bip01_R_Finger2" 1.719575 -0.000005 0 0 -0.007974 -0.366436 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Finger22" "ValveBiped.Bip01_R_Finger21" 1.209182 -0.000001 0 0 -0.004461 -0.216376 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Finger1" "ValveBiped.Bip01_R_Hand" 3.859828 -0.148935 -1.331282 -0.354419 0.038567 -0.532001 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Finger11" "ValveBiped.Bip01_R_Finger1" 1.719425 0 0 0 -0.006613 -0.36297 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Finger12" "ValveBiped.Bip01_R_Finger11" 1.099665 0 0 0 -0.004211 -0.244312 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Finger0" "ValveBiped.Bip01_R_Hand" 0.806014 -0.359835 -1.318334 1.2042 0.673618 -0.793956 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Finger01" "ValveBiped.Bip01_R_Finger0" 1.789783 0.000001 0 0 -0.006301 0.228555 0 0 0 0 0 0
$definebone "ValveBiped.Bip01_R_Finger02" "ValveBiped.Bip01_R_Finger01" 1.207003 0 0.000004 0 -0.009618 0.362905 0 0 0 0 0 0
$definebone "ValveBiped.baton_parent" "ValveBiped.Bip01_R_Hand" 2.338454 -1.535743 -6.391511 1.520245 -0.09438 -2.001951 0 0 0 0 0 0

$weightlist "shild_arm" {
	 "ValveBiped.Bip01_Pelvis" 0
	 "ValveBiped.Bip01_Spine" 0
	 "ValveBiped.Bip01_Spine1" 0
	 "ValveBiped.Bip01_Spine2" 0
	 "ValveBiped.Bip01_Spine4" 0
	 "ValveBiped.Bip01_Neck1" 0
	 "ValveBiped.Bip01_Head1" 0
	 "ValveBiped.forward" 0
	 "ValveBiped.Bip01_R_Clavicle" 0
	 "ValveBiped.Bip01_R_UpperArm" 0
	 "ValveBiped.Bip01_R_Forearm" 0
	 "ValveBiped.Bip01_R_Hand" 0
	 "ValveBiped.Anim_Attachment_RH" 0
	 "ValveBiped.Bip01_L_Clavicle" 0
	 "ValveBiped.Bip01_L_UpperArm" 0.8
	 "ValveBiped.Bip01_L_Forearm" 1
	 "ValveBiped.Bip01_L_Hand" 1
	 "ValveBiped.Anim_Attachment_LH" 0
	 "ValveBiped.Bip01_R_Thigh" 0
	 //"ValveBiped.Bip01_R_Calf" 0
	 //"ValveBiped.Bip01_R_Foot" 0
	 //"ValveBiped.Bip01_R_Toe0" 0
	 //"ValveBiped.Bip01_L_Thigh" 0
	 //"ValveBiped.Bip01_L_Calf" 0
	 //"ValveBiped.Bip01_L_Foot" 0
	 //"ValveBiped.Bip01_L_Toe0" 0
	 //"ValveBiped.Bip01_L_Finger4" 0
	 //"ValveBiped.Bip01_L_Finger41" 0
	 //"ValveBiped.Bip01_L_Finger42" 0
	 //"ValveBiped.Bip01_L_Finger3" 0
	 //"ValveBiped.Bip01_L_Finger31" 0
	 //"ValveBiped.Bip01_L_Finger32" 0
	 //"ValveBiped.Bip01_L_Finger2" 0
	 //"ValveBiped.Bip01_L_Finger21" 0
	 // "ValveBiped.Bip01_L_Finger22" 0
	 // "ValveBiped.Bip01_L_Finger1" 0
	 // "ValveBiped.Bip01_L_Finger11" 0
	 // "ValveBiped.Bip01_L_Finger12" 0
	 // "ValveBiped.Bip01_L_Finger0" 0
	 // "ValveBiped.Bip01_L_Finger01" 0
	 // "ValveBiped.Bip01_L_Finger02" 0
	 // "ValveBiped.Bip01_R_Finger4" 0
	 // "ValveBiped.Bip01_R_Finger41" 0
	 // "ValveBiped.Bip01_R_Finger42" 0
	 // "ValveBiped.Bip01_R_Finger3" 0
	 // "ValveBiped.Bip01_R_Finger31" 0
	 //"ValveBiped.Bip01_R_Finger32" 0
	 //"ValveBiped.Bip01_R_Finger2" 0
	 //"ValveBiped.Bip01_R_Finger21" 0
	 //"ValveBiped.Bip01_R_Finger22" 0
	 //"ValveBiped.Bip01_R_Finger1" 0
	 //"ValveBiped.Bip01_R_Finger11" 0
	 //"ValveBiped.Bip01_R_Finger12" 0
	 //"ValveBiped.Bip01_R_Finger0" 0
	 //"ValveBiped.Bip01_R_Finger01" 0
	 //"ValveBiped.Bip01_R_Finger02" 0
	 "ValveBiped.baton_parent" 0
}

$animation "a_RunS" "Police_animations_anims\a_RunS.smd" {
	fps 28
	loop
}
$animation "a_RunSE" "Police_animations_anims\a_RunSE.smd" {
	fps 33
	loop
}
$animation "a_RunE" "Police_animations_anims\a_RunE.smd" {
	fps 29
	loop
}
$animation "a_RunNE" "Police_animations_anims\a_RunNE.smd" {
	fps 35
	loop
}
$animation "a_RunN" "Police_animations_anims\a_RunN.smd" {
	fps 30
	loop
}
$animation "a_RunNW" "Police_animations_anims\a_RunNW.smd" {
	fps 35
	loop
}
$animation "a_RunW" "Police_animations_anims\a_RunW.smd" {
	fps 29
	loop
}
$animation "a_RunSW" "Police_animations_anims\a_RunSW.smd" {
	fps 33
	loop
}

$animation "zero" "Police_animations_pg\ragdoll.smd" {
	fps 30
}

$animation "pg_holdshild" "Police_animations_pg\hold_shild.smd" {
	fps 30
	weightlist shild_arm
	//subtract "zero" 0
}

$sequence "holdshild" "pg_holdshild"{
	loop
	hidden
}



$sequence "batonshildidle1" "Police_animations_anims\batonidle1.smd" {
	fps 30
	activity "ACT_IDLE_HOLD_SHILD" 1
	loop
	addlayer holdshild
	node "standing_baton"
}

$sequence "batonshildangryidle1" "Police_animations_anims\batonangryidle1.smd" {
	fps 30
	activity "ACT_IDLE_ANGRY_HOLD_SHILD" 1
	loop
	addlayer holdshild
	node "standing_baton"
}

$sequence "swingbatonshild" "Police_animations_anims\swing.smd" {
	fps 35
	activity "ACT_MELEE_ATTACK_SWING_SHILD" 1
	addlayer holdshild
	{ event 3001 13 "" }
}

$sequence "run_all_shild" {
	"a_RunS"
	"a_RunSE"
	"a_RunE"
	"a_RunNE"
	"a_RunN"
	"a_RunNW"
	"a_RunW"
	"a_RunSW"
	"a_RunS"
	fps 28
	activity "ACT_RUN_SHILD" 1
	loop
	blendwidth 9
	addlayer holdshild
	blend "move_yaw" -180 180
	{ event 6004 7 "NPC_MetroPolice" }
	{ event 6005 16 "NPC_MetroPolice" }
}