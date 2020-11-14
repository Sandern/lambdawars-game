// Created by Crowbar 0.24.0.0

$modelname "Police_animations.mdl"

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


// NOTE: The following commented-out $definebone lines might be needed, as is often the case for view models. When needed, simply remove the two slashes '//' from the start of each line.
// $definebone "ValveBiped.Bip01_Pelvis" "" -0.000005 -0.533615 38.566917 1.570796 0 0 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_Spine" "ValveBiped.Bip01_Pelvis" 0.000005 3.345128 -2.981901 1.570796 0.086293 1.570796 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_Spine1" "ValveBiped.Bip01_Spine" 4.018331 0 0 0 0 -0.029242 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_Spine2" "ValveBiped.Bip01_Spine1" 3.518565 0 0 0 0 0.100336 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_Spine4" "ValveBiped.Bip01_Spine2" 8.942642 0 0 0 0 0.194096 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_Neck1" "ValveBiped.Bip01_Spine4" 3.307271 0 0 3.14159 0 0.400478 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_Head1" "ValveBiped.Bip01_Neck1" 3.593712 -0.000001 0 0 -0.000001 0.406587 0 0 0 0 0 0
// $definebone "ValveBiped.forward" "ValveBiped.Bip01_Head1" 1.999997 -3.000001 0 -1.570796 0 -1.32645 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Clavicle" "ValveBiped.Bip01_Spine4" 2.03335 1.000771 -1.93761 -1.668474 1.286518 2.942953 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_UpperArm" "ValveBiped.Bip01_R_Clavicle" 6.028143 0.000002 0 1.639479 -0.008065 -0.586846 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Forearm" "ValveBiped.Bip01_R_UpperArm" 11.692549 0 0.000002 0 0 -0.060372 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Hand" "ValveBiped.Bip01_R_Forearm" 11.481698 0 0 -1.564937 0.106606 0.044193 0 0 0 0 0 0
// $definebone "ValveBiped.Anim_Attachment_RH" "ValveBiped.Bip01_R_Hand" 2.676087 -1.71244 0 -1.570796 0 -1.570796 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Clavicle" "ValveBiped.Bip01_Spine4" 2.033342 1.000767 1.93766 1.596637 -1.286515 2.942961 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_UpperArm" "ValveBiped.Bip01_L_Clavicle" 6.028142 0.000002 0 -1.579613 0.047801 -0.585173 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Forearm" "ValveBiped.Bip01_L_UpperArm" 11.692555 0 0.000005 0 0 -0.060372 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Hand" "ValveBiped.Bip01_L_Forearm" 11.481671 0 -0.00003 1.573183 -0.106613 0.044193 0 0 0 0 0 0
// $definebone "ValveBiped.Anim_Attachment_LH" "ValveBiped.Bip01_L_Hand" 2.676088 -1.712441 0 1.570797 0 1.570797 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Thigh" "ValveBiped.Bip01_Pelvis" -3.890452 0.000004 0.000007 -1.570796 0.051845 -1.576021 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Calf" "ValveBiped.Bip01_R_Thigh" 17.848171 0 0 0 0 0.034187 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Foot" "ValveBiped.Bip01_R_Calf" 16.525253 0 0 0.038611 0.040779 -1.071632 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Toe0" "ValveBiped.Bip01_R_Foot" 6.879454 0 0 -0.081333 -0.002951 -0.584373 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Thigh" "ValveBiped.Bip01_Pelvis" 3.890452 -0.000004 -0.000003 -1.570796 0.051839 -1.565574 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Calf" "ValveBiped.Bip01_L_Thigh" 17.848175 0 0 0 0 0.0342 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Foot" "ValveBiped.Bip01_L_Calf" 16.525249 0 0 -0.027915 -0.040782 -1.071638 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Toe0" "ValveBiped.Bip01_L_Foot" 6.879452 0 0 -0.007299 -0.00295 -0.584374 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger4" "ValveBiped.Bip01_L_Hand" 3.859704 -0.142404 -1.191975 -0.479144 0.15219 -0.879874 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger41" "ValveBiped.Bip01_L_Finger4" 1.312563 0.000001 0.000001 0 0.009665 -0.43972 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger42" "ValveBiped.Bip01_L_Finger41" 0.729362 0.000002 0 0 0.004971 -0.244299 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger3" "ValveBiped.Bip01_L_Hand" 3.942327 0.046774 -0.431443 -0.155014 0.073328 -0.810648 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger31" "ValveBiped.Bip01_L_Finger3" 1.539092 0.000002 0 0 0.00446 -0.247797 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger32" "ValveBiped.Bip01_L_Finger31" 1.196319 -0.000001 0 0 0.007361 -0.430802 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger2" "ValveBiped.Bip01_L_Hand" 3.883689 -0.046767 0.431443 0.085902 0.02183 -0.587867 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger21" "ValveBiped.Bip01_L_Finger2" 1.719575 0.000002 0 0 0.005516 -0.366478 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger22" "ValveBiped.Bip01_L_Finger21" 1.209182 -0.000001 0 0 0.003084 -0.2164 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger1" "ValveBiped.Bip01_L_Hand" 3.859859 -0.13795 1.332466 0.354449 -0.04275 -0.531718 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger11" "ValveBiped.Bip01_L_Finger1" 1.719429 0.000003 0 0 0.004074 -0.363009 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger12" "ValveBiped.Bip01_L_Finger11" 1.099668 0.000001 0 0 0.002596 -0.244331 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger0" "ValveBiped.Bip01_L_Hand" 0.806048 -0.348923 1.321258 -1.206854 -0.679488 -0.789308 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger01" "ValveBiped.Bip01_L_Finger0" 1.789785 0 0.000002 0 0.007387 0.228523 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_L_Finger02" "ValveBiped.Bip01_L_Finger01" 1.206998 0 0 0 0.011267 0.36286 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger4" "ValveBiped.Bip01_R_Hand" 3.859672 -0.132566 1.193108 0.47914 -0.158545 -0.879041 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger41" "ValveBiped.Bip01_R_Finger4" 1.31256 0 -0.000001 0 -0.011932 -0.439672 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger42" "ValveBiped.Bip01_R_Finger41" 0.729361 0.000002 0 0 -0.006134 -0.244271 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger3" "ValveBiped.Bip01_R_Hand" 3.942293 0.05033 0.431043 0.154999 -0.079305 -0.810205 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger31" "ValveBiped.Bip01_R_Finger3" 1.539095 0.000003 0 0 -0.005854 -0.247771 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger32" "ValveBiped.Bip01_R_Finger31" 1.196323 0 0 0 -0.009663 -0.430761 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger2" "ValveBiped.Bip01_R_Hand" 3.883655 -0.050326 -0.431043 -0.085905 -0.026404 -0.587695 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger21" "ValveBiped.Bip01_R_Finger2" 1.719575 -0.000005 0 0 -0.007974 -0.366436 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger22" "ValveBiped.Bip01_R_Finger21" 1.209182 -0.000001 0 0 -0.004461 -0.216376 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger1" "ValveBiped.Bip01_R_Hand" 3.859828 -0.148935 -1.331282 -0.354419 0.038567 -0.532001 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger11" "ValveBiped.Bip01_R_Finger1" 1.719425 0 0 0 -0.006613 -0.36297 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger12" "ValveBiped.Bip01_R_Finger11" 1.099665 0 0 0 -0.004211 -0.244312 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger0" "ValveBiped.Bip01_R_Hand" 0.806014 -0.359835 -1.318334 1.2042 0.673618 -0.793956 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger01" "ValveBiped.Bip01_R_Finger0" 1.789783 0.000001 0 0 -0.006301 0.228555 0 0 0 0 0 0
// $definebone "ValveBiped.Bip01_R_Finger02" "ValveBiped.Bip01_R_Finger01" 1.207003 0 0.000004 0 -0.009618 0.362905 0 0 0 0 0 0
// $definebone "ValveBiped.baton_parent" "ValveBiped.Bip01_R_Hand" 2.338454 -1.535743 -6.391511 1.520245 -0.09438 -2.001951 0 0 0 0 0 0

// The 32 below is a guess until further is known about the format.
$animblocksize 32

$sectionframes 30 120

// $weightlist "weights_body_rot_z" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_spine_rot_z" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_neck_trans_x" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_head_rot_z" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_head_rot_y" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_head_rot_x" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_gesture_reload_pistolspine" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_gesture_reload_pistolarms" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_gesture_reload_pistol" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_gesture_reload_smg1spine" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_gesture_reload_smg1arms" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_gesture_reload_smg1" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_swinggesturespine" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_swinggesturearms" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_swinggesture" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_pistol_Aim_all" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_WalkN_pistol_Aim_all" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_SMG1_Aim_all" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_WalkN_SMG1_Aim_all" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_layer_walk_hold_baton_angry" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_Pistol_aim_walk_all_delta" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_layer_walk_aiming_pistol" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_layer_walk_hold_pistol" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_SMG1_aim_walk_all_delta" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_layer_walk_aiming_SMG1" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_layer_walk_hold_smg1" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_Pistol_aim_run_all_delta" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_layer_run_hold_pistol" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_layer_run_aiming_pistol" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_smg1_aim_run_all_delta" {
// 	 "ValveBiped.Bip01_Pelvis" 1
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_layer_run_hold_smg1" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_layer_run_aiming_smg1" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 1
// 	 "ValveBiped.Bip01_Spine1" 1
// 	 "ValveBiped.Bip01_Spine2" 1
// 	 "ValveBiped.Bip01_Spine4" 1
// 	 "ValveBiped.Bip01_Neck1" 1
// 	 "ValveBiped.Bip01_Head1" 1
// 	 "ValveBiped.forward" 1
// 	 "ValveBiped.Bip01_R_Clavicle" 1
// 	 "ValveBiped.Bip01_R_UpperArm" 1
// 	 "ValveBiped.Bip01_R_Forearm" 1
// 	 "ValveBiped.Bip01_R_Hand" 1
// 	 "ValveBiped.Anim_Attachment_RH" 1
// 	 "ValveBiped.Bip01_L_Clavicle" 1
// 	 "ValveBiped.Bip01_L_UpperArm" 1
// 	 "ValveBiped.Bip01_L_Forearm" 1
// 	 "ValveBiped.Bip01_L_Hand" 1
// 	 "ValveBiped.Anim_Attachment_LH" 1
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 1
// 	 "ValveBiped.Bip01_L_Finger41" 1
// 	 "ValveBiped.Bip01_L_Finger42" 1
// 	 "ValveBiped.Bip01_L_Finger3" 1
// 	 "ValveBiped.Bip01_L_Finger31" 1
// 	 "ValveBiped.Bip01_L_Finger32" 1
// 	 "ValveBiped.Bip01_L_Finger2" 1
// 	 "ValveBiped.Bip01_L_Finger21" 1
// 	 "ValveBiped.Bip01_L_Finger22" 1
// 	 "ValveBiped.Bip01_L_Finger1" 1
// 	 "ValveBiped.Bip01_L_Finger11" 1
// 	 "ValveBiped.Bip01_L_Finger12" 1
// 	 "ValveBiped.Bip01_L_Finger0" 1
// 	 "ValveBiped.Bip01_L_Finger01" 1
// 	 "ValveBiped.Bip01_L_Finger02" 1
// 	 "ValveBiped.Bip01_R_Finger4" 1
// 	 "ValveBiped.Bip01_R_Finger41" 1
// 	 "ValveBiped.Bip01_R_Finger42" 1
// 	 "ValveBiped.Bip01_R_Finger3" 1
// 	 "ValveBiped.Bip01_R_Finger31" 1
// 	 "ValveBiped.Bip01_R_Finger32" 1
// 	 "ValveBiped.Bip01_R_Finger2" 1
// 	 "ValveBiped.Bip01_R_Finger21" 1
// 	 "ValveBiped.Bip01_R_Finger22" 1
// 	 "ValveBiped.Bip01_R_Finger1" 1
// 	 "ValveBiped.Bip01_R_Finger11" 1
// 	 "ValveBiped.Bip01_R_Finger12" 1
// 	 "ValveBiped.Bip01_R_Finger0" 1
// 	 "ValveBiped.Bip01_R_Finger01" 1
// 	 "ValveBiped.Bip01_R_Finger02" 1
// 	 "ValveBiped.baton_parent" 1
// }
// $weightlist "weights_turnleft" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_turnright" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_gesture_turn_left_45" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_gesture_turn_left_90" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_gesture_turn_right_45" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }
// $weightlist "weights_gesture_turn_right_90" {
// 	 "ValveBiped.Bip01_Pelvis" 0
// 	 "ValveBiped.Bip01_Spine" 0
// 	 "ValveBiped.Bip01_Spine1" 0
// 	 "ValveBiped.Bip01_Spine2" 0
// 	 "ValveBiped.Bip01_Spine4" 0
// 	 "ValveBiped.Bip01_Neck1" 0
// 	 "ValveBiped.Bip01_Head1" 0
// 	 "ValveBiped.forward" 0
// 	 "ValveBiped.Bip01_R_Clavicle" 0
// 	 "ValveBiped.Bip01_R_UpperArm" 0
// 	 "ValveBiped.Bip01_R_Forearm" 0
// 	 "ValveBiped.Bip01_R_Hand" 0
// 	 "ValveBiped.Anim_Attachment_RH" 0
// 	 "ValveBiped.Bip01_L_Clavicle" 0
// 	 "ValveBiped.Bip01_L_UpperArm" 0
// 	 "ValveBiped.Bip01_L_Forearm" 0
// 	 "ValveBiped.Bip01_L_Hand" 0
// 	 "ValveBiped.Anim_Attachment_LH" 0
// 	 "ValveBiped.Bip01_R_Thigh" 0
// 	 "ValveBiped.Bip01_R_Calf" 0
// 	 "ValveBiped.Bip01_R_Foot" 0
// 	 "ValveBiped.Bip01_R_Toe0" 0
// 	 "ValveBiped.Bip01_L_Thigh" 0
// 	 "ValveBiped.Bip01_L_Calf" 0
// 	 "ValveBiped.Bip01_L_Foot" 0
// 	 "ValveBiped.Bip01_L_Toe0" 0
// 	 "ValveBiped.Bip01_L_Finger4" 0
// 	 "ValveBiped.Bip01_L_Finger41" 0
// 	 "ValveBiped.Bip01_L_Finger42" 0
// 	 "ValveBiped.Bip01_L_Finger3" 0
// 	 "ValveBiped.Bip01_L_Finger31" 0
// 	 "ValveBiped.Bip01_L_Finger32" 0
// 	 "ValveBiped.Bip01_L_Finger2" 0
// 	 "ValveBiped.Bip01_L_Finger21" 0
// 	 "ValveBiped.Bip01_L_Finger22" 0
// 	 "ValveBiped.Bip01_L_Finger1" 0
// 	 "ValveBiped.Bip01_L_Finger11" 0
// 	 "ValveBiped.Bip01_L_Finger12" 0
// 	 "ValveBiped.Bip01_L_Finger0" 0
// 	 "ValveBiped.Bip01_L_Finger01" 0
// 	 "ValveBiped.Bip01_L_Finger02" 0
// 	 "ValveBiped.Bip01_R_Finger4" 0
// 	 "ValveBiped.Bip01_R_Finger41" 0
// 	 "ValveBiped.Bip01_R_Finger42" 0
// 	 "ValveBiped.Bip01_R_Finger3" 0
// 	 "ValveBiped.Bip01_R_Finger31" 0
// 	 "ValveBiped.Bip01_R_Finger32" 0
// 	 "ValveBiped.Bip01_R_Finger2" 0
// 	 "ValveBiped.Bip01_R_Finger21" 0
// 	 "ValveBiped.Bip01_R_Finger22" 0
// 	 "ValveBiped.Bip01_R_Finger1" 0
// 	 "ValveBiped.Bip01_R_Finger11" 0
// 	 "ValveBiped.Bip01_R_Finger12" 0
// 	 "ValveBiped.Bip01_R_Finger0" 0
// 	 "ValveBiped.Bip01_R_Finger01" 0
// 	 "ValveBiped.Bip01_R_Finger02" 0
// 	 "ValveBiped.baton_parent" 0
// }

$animation "a_pose_neutral" "Police_animations_anims\a_pose_neutral.smd" {
	fps 30
}
$animation "a_body_rot" "Police_animations_anims\a_body_rot.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_body_rot_z"
}
$animation "a_body_rot_z_rt" "Police_animations_anims\a_body_rot_z_rt.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_body_rot_z"
}
$animation "a_body_rot_z_lt" "Police_animations_anims\a_body_rot_z_lt.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_body_rot_z"
}
$animation "a_spine_rot" "Police_animations_anims\a_spine_rot.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_spine_rot_z"
}
$animation "a_spine_rot_z_rt" "Police_animations_anims\a_spine_rot_z_rt.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_spine_rot_z"
}
$animation "a_spine_rot_z_lt" "Police_animations_anims\a_spine_rot_z_lt.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_spine_rot_z"
}
$animation "a_head_rot" "Police_animations_anims\a_head_rot.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_head_rot_z"
}
$animation "a_head_rot_lt" "Police_animations_anims\a_head_rot_lt.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_head_rot_x"
}
$animation "a_head_rot_rt" "Police_animations_anims\a_head_rot_rt.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_head_rot_x"
}
$animation "a_neck_trans" "Police_animations_anims\a_neck_trans.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_neck_trans_x"
}
$animation "a_neck_trans_fwd" "Police_animations_anims\a_neck_trans_fwd.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_neck_trans_x"
}
$animation "a_neck_trans_back" "Police_animations_anims\a_neck_trans_back.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_neck_trans_x"
}
$animation "a_head_rot_dwn" "Police_animations_anims\a_head_rot_dwn.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_head_rot_y"
}
$animation "a_head_rot_up" "Police_animations_anims\a_head_rot_up.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_head_rot_y"
}
$animation "a_head_rot_z_rt" "Police_animations_anims\a_head_rot_z_rt.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_head_rot_z"
}
$animation "a_head_rot_z_lt" "Police_animations_anims\a_head_rot_z_lt.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_head_rot_z"
}
$animation "a_flinch_gesture" "Police_animations_anims\a_flinch_gesture.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}
$animation "a_flinch_head_gesture1" "Police_animations_anims\a_flinch_head_gesture1.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}
$animation "a_flinch_head_gesture2" "Police_animations_anims\a_flinch_head_gesture2.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}
$animation "a_flinch_gut_gesture1" "Police_animations_anims\a_flinch_gut_gesture1.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}
$animation "a_flinch_gut_gesture2" "Police_animations_anims\a_flinch_gut_gesture2.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}
$animation "a_flinch_larm_gesture" "Police_animations_anims\a_flinch_larm_gesture.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}
$animation "a_flinch_rarm_gesture" "Police_animations_anims\a_flinch_rarm_gesture.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}
$animation "a_aim_pistol_neutral" "Police_animations_anims\a_aim_pistol_neutral.smd" {
	fps 30
}
$animation "a_pistol_aim_down_left" "Police_animations_anims\a_pistol_aim_down_left.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_pistol_Aim_all"
}
$animation "a_pistol_aim_down_center" "Police_animations_anims\a_pistol_aim_down_center.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_pistol_Aim_all"
}
$animation "a_pistol_aim_down_right" "Police_animations_anims\a_pistol_aim_down_right.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_pistol_Aim_all"
}
$animation "a_pistol_aim_mid_left" "Police_animations_anims\a_pistol_aim_mid_left.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_pistol_Aim_all"
}
$animation "a_pistol_aim_mid_center" "Police_animations_anims\a_pistol_aim_mid_center.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_pistol_Aim_all"
}
$animation "a_pistol_aim_mid_right" "Police_animations_anims\a_pistol_aim_mid_right.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_pistol_Aim_all"
}
$animation "a_pistol_aim_up_left" "Police_animations_anims\a_pistol_aim_up_left.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_pistol_Aim_all"
}
$animation "a_pistol_aim_up_center" "Police_animations_anims\a_pistol_aim_up_center.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_pistol_Aim_all"
}
$animation "a_pistol_aim_up_right" "Police_animations_anims\a_pistol_aim_up_right.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_pistol_Aim_all"
}
$animation "a_pistol_aim_straight_up" "Police_animations_anims\a_pistol_aim_straight_up.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_pistol_Aim_all"
}
$animation "a_walkn_aim_pistol_neutral" "Police_animations_anims\a_walkn_aim_pistol_neutral.smd" {
	fps 30
}
$animation "a_WalkN_pistol_aim_down_left" "Police_animations_anims\a_WalkN_pistol_aim_down_left.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_pistol_Aim_all"
}
$animation "a_WalkN_pistol_aim_down_center" "Police_animations_anims\a_WalkN_pistol_aim_down_center.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_pistol_Aim_all"
}
$animation "a_WalkN_pistol_aim_down_right" "Police_animations_anims\a_WalkN_pistol_aim_down_right.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_pistol_Aim_all"
}
$animation "a_WalkN_pistol_aim_mid_left" "Police_animations_anims\a_WalkN_pistol_aim_mid_left.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_pistol_Aim_all"
}
$animation "a_WalkN_pistol_aim_mid_center" "Police_animations_anims\a_WalkN_pistol_aim_mid_center.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_pistol_Aim_all"
}
$animation "a_WalkN_pistol_aim_mid_right" "Police_animations_anims\a_WalkN_pistol_aim_mid_right.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_pistol_Aim_all"
}
$animation "a_WalkN_pistol_aim_up_left" "Police_animations_anims\a_WalkN_pistol_aim_up_left.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_pistol_Aim_all"
}
$animation "a_WalkN_pistol_aim_up_center" "Police_animations_anims\a_WalkN_pistol_aim_up_center.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_pistol_Aim_all"
}
$animation "a_WalkN_pistol_aim_up_right" "Police_animations_anims\a_WalkN_pistol_aim_up_right.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_pistol_Aim_all"
}
$animation "a_WalkN_pistol_aim_straight_up" "Police_animations_anims\a_WalkN_pistol_aim_straight_up.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_pistol_Aim_all"
}
$animation "a_aim_SMG1_neutral" "Police_animations_anims\a_aim_SMG1_neutral.smd" {
	fps 30
}
$animation "a_SMG1_aim_down_left" "Police_animations_anims\a_SMG1_aim_down_left.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_Aim_all"
}
$animation "a_SMG1_aim_down_center" "Police_animations_anims\a_SMG1_aim_down_center.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_Aim_all"
}
$animation "a_SMG1_aim_down_right" "Police_animations_anims\a_SMG1_aim_down_right.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_Aim_all"
}
$animation "a_SMG1_aim_mid_left" "Police_animations_anims\a_SMG1_aim_mid_left.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_Aim_all"
}
$animation "a_SMG1_aim_mid_center" "Police_animations_anims\a_SMG1_aim_mid_center.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_Aim_all"
}
$animation "a_SMG1_aim_mid_right" "Police_animations_anims\a_SMG1_aim_mid_right.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_Aim_all"
}
$animation "a_SMG1_aim_up_left" "Police_animations_anims\a_SMG1_aim_up_left.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_Aim_all"
}
$animation "a_SMG1_aim_up_center" "Police_animations_anims\a_SMG1_aim_up_center.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_Aim_all"
}
$animation "a_SMG1_aim_up_right" "Police_animations_anims\a_SMG1_aim_up_right.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_Aim_all"
}
$animation "a_SMG1_aim_straight_up" "Police_animations_anims\a_SMG1_aim_straight_up.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_Aim_all"
}
$animation "a_walkn_aim_SMG1_neutral" "Police_animations_anims\a_walkn_aim_SMG1_neutral.smd" {
	fps 30
}
$animation "a_WalkN_SMG1_aim_down_left" "Police_animations_anims\a_WalkN_SMG1_aim_down_left.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_SMG1_Aim_all"
}
$animation "a_WalkN_SMG1_aim_down_center" "Police_animations_anims\a_WalkN_SMG1_aim_down_center.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_SMG1_Aim_all"
}
$animation "a_WalkN_SMG1_aim_down_right" "Police_animations_anims\a_WalkN_SMG1_aim_down_right.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_SMG1_Aim_all"
}
$animation "a_WalkN_SMG1_aim_mid_left" "Police_animations_anims\a_WalkN_SMG1_aim_mid_left.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_SMG1_Aim_all"
}
$animation "a_WalkN_SMG1_aim_mid_center" "Police_animations_anims\a_WalkN_SMG1_aim_mid_center.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_SMG1_Aim_all"
}
$animation "a_WalkN_SMG1_aim_mid_right" "Police_animations_anims\a_WalkN_SMG1_aim_mid_right.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_SMG1_Aim_all"
}
$animation "a_WalkN_SMG1_aim_up_left" "Police_animations_anims\a_WalkN_SMG1_aim_up_left.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_SMG1_Aim_all"
}
$animation "a_WalkN_SMG1_aim_up_center" "Police_animations_anims\a_WalkN_SMG1_aim_up_center.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_SMG1_Aim_all"
}
$animation "a_WalkN_SMG1_aim_up_right" "Police_animations_anims\a_WalkN_SMG1_aim_up_right.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_SMG1_Aim_all"
}
$animation "a_WalkN_SMG1_aim_straight_up" "Police_animations_anims\a_WalkN_SMG1_aim_straight_up.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_WalkN_SMG1_Aim_all"
}
$animation "a_Crouch_walkS" "Police_animations_anims\a_Crouch_walkS.smd" {
	fps 30
	loop
}
$animation "a_Crouch_walkSE" "Police_animations_anims\a_Crouch_walkSE.smd" {
	fps 30
	loop
}
$animation "a_Crouch_walkE" "Police_animations_anims\a_Crouch_walkE.smd" {
	fps 30
	loop
}
$animation "a_Crouch_walkNE" "Police_animations_anims\a_Crouch_walkNE.smd" {
	fps 30
	loop
}
$animation "a_Crouch_walkN" "Police_animations_anims\a_Crouch_walkN.smd" {
	fps 30
	loop
}
$animation "a_Crouch_walkNW" "Police_animations_anims\a_Crouch_walkNW.smd" {
	fps 30
	loop
}
$animation "a_Crouch_walkW" "Police_animations_anims\a_Crouch_walkW.smd" {
	fps 30
	loop
}
$animation "a_Crouch_walkSW" "Police_animations_anims\a_Crouch_walkSW.smd" {
	fps 30
	loop
}
$animation "a_WalkS" "Police_animations_anims\a_WalkS.smd" {
	fps 31
	loop
}
$animation "a_WalkSE" "Police_animations_anims\a_WalkSE.smd" {
	fps 29
	loop
}
$animation "a_WalkE" "Police_animations_anims\a_WalkE.smd" {
	fps 33
	loop
}
$animation "a_WalkNE" "Police_animations_anims\a_WalkNE.smd" {
	fps 32
	loop
}
$animation "a_WalkN" "Police_animations_anims\a_WalkN.smd" {
	fps 30
	loop
}
$animation "a_WalkNW" "Police_animations_anims\a_WalkNW.smd" {
	fps 32
	loop
}
$animation "a_WalkW" "Police_animations_anims\a_WalkW.smd" {
	fps 33
	loop
}
$animation "a_WalkSW" "Police_animations_anims\a_WalkSW.smd" {
	fps 29
	loop
}
$animation "a_walkN_hold_baton_angry" "Police_animations_anims\a_walkN_hold_baton_angry.smd" {
	fps 30
	loop
}
$animation "a_walkS_pistol_aim_delta" "Police_animations_anims\a_walkS_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_walk_all_delta"
}
$animation "a_walkSE_pistol_aim_delta" "Police_animations_anims\a_walkSE_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_walk_all_delta"
}
$animation "a_walkE_pistol_aim_delta" "Police_animations_anims\a_walkE_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_walk_all_delta"
}
$animation "a_walkNE_pistol_aim_delta" "Police_animations_anims\a_walkNE_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_walk_all_delta"
}
$animation "a_walkN_pistol_aim_delta" "Police_animations_anims\a_walkN_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_walk_all_delta"
}
$animation "a_walkNW_pistol_aim_delta" "Police_animations_anims\a_walkNW_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_walk_all_delta"
}
$animation "a_walkW_pistol_aim_delta" "Police_animations_anims\a_walkW_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_walk_all_delta"
}
$animation "a_walkSW_pistol_aim_delta" "Police_animations_anims\a_walkSW_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_walk_all_delta"
}
$animation "a_WalkN_aim_pistol" "Police_animations_anims\a_WalkN_aim_pistol.smd" {
	fps 30
	loop
}
$animation "a_walkN_hold_pistol" "Police_animations_anims\a_walkN_hold_pistol.smd" {
	fps 30
	loop
}
$animation "a_walkS_SMG1_aim_delta" "Police_animations_anims\a_walkS_SMG1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_aim_walk_all_delta"
}
$animation "a_walkSE_SMG1_aim_delta" "Police_animations_anims\a_walkSE_SMG1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_aim_walk_all_delta"
}
$animation "a_walkE_SMG1_aim_delta" "Police_animations_anims\a_walkE_SMG1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_aim_walk_all_delta"
}
$animation "a_walkNE_SMG1_aim_delta" "Police_animations_anims\a_walkNE_SMG1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_aim_walk_all_delta"
}
$animation "a_walkN_SMG1_aim_delta" "Police_animations_anims\a_walkN_SMG1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_aim_walk_all_delta"
}
$animation "a_walkNW_SMG1_aim_delta" "Police_animations_anims\a_walkNW_SMG1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_aim_walk_all_delta"
}
$animation "a_walkW_SMG1_aim_delta" "Police_animations_anims\a_walkW_SMG1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_aim_walk_all_delta"
}
$animation "a_walkSW_SMG1_aim_delta" "Police_animations_anims\a_walkSW_SMG1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_SMG1_aim_walk_all_delta"
}
$animation "a_WalkN_aim_SMG1" "Police_animations_anims\a_WalkN_aim_SMG1.smd" {
	fps 30
	loop
}
$animation "a_walkN_hold_smg1" "Police_animations_anims\a_walkN_hold_smg1.smd" {
	fps 30
	loop
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
$animation "a_runS_pistol_aim_delta" "Police_animations_anims\a_runS_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_run_all_delta"
}
$animation "a_runSE_pistol_aim_delta" "Police_animations_anims\a_runSE_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_run_all_delta"
}
$animation "a_runE_pistol_aim_delta" "Police_animations_anims\a_runE_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_run_all_delta"
}
$animation "a_runNE_pistol_aim_delta" "Police_animations_anims\a_runNE_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_run_all_delta"
}
$animation "a_runN_pistol_aim_delta" "Police_animations_anims\a_runN_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_run_all_delta"
}
$animation "a_runNW_pistol_aim_delta" "Police_animations_anims\a_runNW_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_run_all_delta"
}
$animation "a_runW_pistol_aim_delta" "Police_animations_anims\a_runW_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_run_all_delta"
}
$animation "a_runSW_pistol_aim_delta" "Police_animations_anims\a_runSW_pistol_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_Pistol_aim_run_all_delta"
}
$animation "a_runN_hold_pistol" "Police_animations_anims\a_runN_hold_pistol.smd" {
	fps 30
	loop
}
$animation "a_runN_aim_pistol" "Police_animations_anims\a_runN_aim_pistol.smd" {
	fps 30
	loop
}
$animation "a_runS_smg1_aim_delta" "Police_animations_anims\a_runS_smg1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_smg1_aim_run_all_delta"
}
$animation "a_runSE_smg1_aim_delta" "Police_animations_anims\a_runSE_smg1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_smg1_aim_run_all_delta"
}
$animation "a_runE_smg1_aim_delta" "Police_animations_anims\a_runE_smg1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_smg1_aim_run_all_delta"
}
$animation "a_runNE_smg1_aim_delta" "Police_animations_anims\a_runNE_smg1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_smg1_aim_run_all_delta"
}
$animation "a_runN_smg1_aim_delta" "Police_animations_anims\a_runN_smg1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_smg1_aim_run_all_delta"
}
$animation "a_runNW_smg1_aim_delta" "Police_animations_anims\a_runNW_smg1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_smg1_aim_run_all_delta"
}
$animation "a_runW_smg1_aim_delta" "Police_animations_anims\a_runW_smg1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_smg1_aim_run_all_delta"
}
$animation "a_runSW_smg1_aim_delta" "Police_animations_anims\a_runSW_smg1_aim_delta.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
	weightlist "weights_smg1_aim_run_all_delta"
}
$animation "a_runN_hold_smg1" "Police_animations_anims\a_runN_hold_smg1.smd" {
	fps 30
	loop
}
$animation "a_runN_aim_smg1" "Police_animations_anims\a_runN_aim_smg1.smd" {
	fps 30
	loop
}
$animation "a_jump_holding_hit" "Police_animations_anims\a_jump_holding_hit.smd" {
	fps 30
}
$animation "Man_Gun_neutral" "Police_animations_anims\Man_Gun_neutral.smd" {
	fps 30
}
$animation "Man_Gun_down_left" "Police_animations_anims\Man_Gun_down_left.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}
$animation "Man_Gun_down_center" "Police_animations_anims\Man_Gun_down_center.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}
$animation "Man_Gun_down_right" "Police_animations_anims\Man_Gun_down_right.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}
$animation "Man_Gun_mid_left" "Police_animations_anims\Man_Gun_mid_left.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}
$animation "Man_Gun_mid_center" "Police_animations_anims\Man_Gun_mid_center.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}
$animation "Man_Gun_mid_right" "Police_animations_anims\Man_Gun_mid_right.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}
$animation "Man_Gun_up_left" "Police_animations_anims\Man_Gun_up_left.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}
$animation "Man_Gun_up_center" "Police_animations_anims\Man_Gun_up_center.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}
$animation "Man_Gun_up_right" "Police_animations_anims\Man_Gun_up_right.smd" {
	fps 30
	// This subtract line guesses the animation name and frame index. There is no way to determine which $animation and which frame was used. Change as needed.
	subtract "a_pose_neutral" 0
}


$sequence "body_rot_z" {
	"a_body_rot_z_lt"
	"a_body_rot"
	"a_body_rot_z_rt"
	fps 30
	delta
	autoplay
	hidden
	blendwidth 3
	blend "body_yaw" 29.73423 -29.73426
}

$sequence "spine_rot_z" {
	"a_spine_rot_z_lt"
	"a_spine_rot"
	"a_spine_rot_z_rt"
	fps 30
	delta
	autoplay
	hidden
	blendwidth 3
	blend "spine_yaw" 30.70848 -30.7085
}

$sequence "neck_trans_x" {
	"a_neck_trans_back"
	"a_neck_trans"
	"a_neck_trans_fwd"
	fps 30
	delta
	autoplay
	hidden
	blendwidth 3
	blend "neck_trans" -0.207508 0.2594
}

$sequence "head_rot_z" {
	"a_head_rot_z_lt"
	"a_head_rot"
	"a_head_rot_z_rt"
	fps 30
	delta
	autoplay
	hidden
	blendwidth 3
	blend "head_yaw" 66.70631 -66.70654
}

$sequence "head_rot_y" {
	"a_head_rot_dwn"
	"a_head_rot"
	"a_head_rot_up"
	fps 30
	delta
	autoplay
	hidden
	blendwidth 3
	blend "head_pitch" 25.37666 -34.86658
}

$sequence "head_rot_x" {
	"a_head_rot_lt"
	"a_head_rot"
	"a_head_rot_rt"
	fps 30
	delta
	autoplay
	hidden
	blendwidth 3
	blend "head_roll" -10.93143 10.85243
}

$sequence "batonidle1" "Police_animations_anims\batonidle1.smd" {
	fps 30
	activity "ACT_IDLE" 2
	loop
	node "standing_baton"
}

$sequence "batonidle2" "Police_animations_anims\batonidle2.smd" {
	fps 30
	activity "ACT_IDLE" 1
	loop
	node "standing_baton"
}

$sequence "smg1idle1" "Police_animations_anims\smg1idle1.smd" {
	fps 30
	activity "ACT_IDLE_SMG1" 2
	loop
	node "standing_smg"
}

$sequence "smg1idle2" "Police_animations_anims\smg1idle2.smd" {
	fps 30
	activity "ACT_IDLE_SMG1" 1
	loop
	node "standing_smg"
}

$sequence "pistolidle1" "Police_animations_anims\pistolidle1.smd" {
	fps 30
	activity "ACT_IDLE_PISTOL" 2
	loop
	node "standing_pistol"
}

$sequence "pistolidle2" "Police_animations_anims\pistolidle2.smd" {
	fps 30
	activity "ACT_IDLE_PISTOL" 1
	loop
	node "standing_pistol"
}

$sequence "Idle_Baton" "Police_animations_anims\Idle_Baton.smd" {
	fps 30
	loop
}

$sequence "BlockEntry" "Police_animations_anims\BlockEntry.smd" {
	fps 30
}

$sequence "buttonright" "Police_animations_anims\buttonright.smd" {
	fps 30
}

$sequence "buttonfront" "Police_animations_anims\buttonfront.smd" {
	fps 30
}

$sequence "buttonleft" "Police_animations_anims\buttonleft.smd" {
	fps 30
}

$sequence "busyidle1" "Police_animations_anims\busyidle1.smd" {
	fps 30
	activity "ACT_BUSY_LEAN_BACK" 1
	loop
}

$sequence "busyidle2" "Police_animations_anims\busyidle2.smd" {
	fps 30
	activity "ACT_BUSY_STAND" 1
	loop
}

$sequence "harassfront1" "Police_animations_anims\harassfront1.smd" {
	fps 30
	activity "ACT_POLICE_HARASS1" 1
}

$sequence "harassfront2" "Police_animations_anims\harassfront2.smd" {
	fps 30
	activity "ACT_POLICE_HARASS2" 1
}

$sequence "pickup" "Police_animations_anims\pickup.smd" {
	fps 30
	activity "ACT_PICKUP_GROUND" 1
	{ event 2040 13 "" }
}

$sequence "point" "Police_animations_anims\point.smd" {
	fps 30
	activity "ACT_METROPOLICE_POINT" 1
	node "standing_pistol"
}

$sequence "idleonfire" "Police_animations_anims\idleonfire.smd" {
	fps 30
	activity "ACT_IDLE_ON_FIRE" 1
	loop
}

$sequence "moveonfire" "Police_animations_anims\moveonfire.smd" {
	fps 30
	activity "ACT_RUN_ON_FIRE" 1
	loop
}

$sequence "rappelloop" "Police_animations_anims\rappelloop.smd" {
	fps 30
	activity "ACT_RAPPEL_LOOP" 1
	loop
}

$sequence "rappelland" "Police_animations_anims\rappelland.smd" {
	fps 30
	activity "ACT_RAPPEL_LAND" 1
}

$sequence "dummy1" "Police_animations_anims\batonidle1.smd" {
	fps 30
	loop
	hidden
}

$sequence "dummy2" "Police_animations_anims\batonidle1.smd" {
	fps 30
	loop
	hidden
}

$sequence "pushplayer" "Police_animations_anims\pushplayer.smd" {
	fps 30
	activity "ACT_PUSH_PLAYER" 1
	{ event AE_METROPOLICE_SHOVE 11 "" }
}

$sequence "activatebaton" "Police_animations_anims\activatebaton.smd" {
	fps 30
	activity "ACT_ACTIVATE_BATON" 1
	{ event AE_METROPOLICE_BATON_ON 7 "" }
}

$sequence "deactivatebaton" "Police_animations_anims\deactivatebaton.smd" {
	fps 30
	activity "ACT_DEACTIVATE_BATON" 1
	{ event AE_METROPOLICE_BATON_OFF 7 "" }
}

$sequence "cower" "Police_animations_anims\cower.smd" {
	fps 35
	activity "ACT_COWER" 1
}

$sequence "flinch_head1" "Police_animations_anims\flinch_head1.smd" {
	fps 30
	activity "ACT_FLINCH_HEAD" 1
}

$sequence "flinch_head2" "Police_animations_anims\flinch_head2.smd" {
	fps 30
	activity "ACT_FLINCH_HEAD" 1
}

$sequence "flinch_stomach1" "Police_animations_anims\flinch_stomach1.smd" {
	fps 30
	activity "ACT_FLINCH_STOMACH" 1
}

$sequence "flinch_stomach2" "Police_animations_anims\flinch_stomach2.smd" {
	fps 30
	activity "ACT_FLINCH_STOMACH" 1
}

$sequence "flinch_leftarm1" "Police_animations_anims\flinch_leftarm1.smd" {
	fps 30
	activity "ACT_FLINCH_LEFTARM" 1
}

$sequence "flinch_rightarm1" "Police_animations_anims\flinch_rightarm1.smd" {
	fps 30
	activity "ACT_FLINCH_RIGHTARM" 1
}

$sequence "flinch_back1" "Police_animations_anims\flinch_back1.smd" {
	fps 30
	activity "ACT_METROPOLICE_FLINCH_BEHIND" 1
}

$sequence "flinch1" "Police_animations_anims\flinch1.smd" {
	fps 30
	activity "ACT_SMALL_FLINCH" 1
}

$sequence "flinch2" "Police_animations_anims\flinch2.smd" {
	fps 30
	activity "ACT_BIG_FLINCH" 1
}

$sequence "flinch_gesture" {
	fps 30
	activity "ACT_GESTURE_SMALL_FLINCH" 1
	delta
}

$sequence "flinchheadgest1" {
	fps 30
	activity "ACT_GESTURE_FLINCH_HEAD" 1
	delta
}

$sequence "flinchheadgest2" {
	fps 30
	activity "ACT_GESTURE_FLINCH_HEAD" 1
	delta
}

$sequence "flinchgutgest1" {
	fps 30
	activity "ACT_GESTURE_FLINCH_STOMACH" 1
	delta
}

$sequence "flinchgutgest2" {
	fps 30
	activity "ACT_GESTURE_FLINCH_STOMACH" 1
	delta
}

$sequence "flinchlarmgest" {
	fps 30
	activity "ACT_GESTURE_FLINCH_LEFTARM" 1
	delta
}

$sequence "flinchrarmgest" {
	fps 30
	activity "ACT_GESTURE_FLINCH_RIGHTARM" 1
	delta
}

$sequence "physflinch1" "Police_animations_anims\physflinch1.smd" {
	fps 30
	activity "ACT_FLINCH_PHYSICS" 1
}

$sequence "physflinch2" "Police_animations_anims\physflinch2.smd" {
	fps 30
	activity "ACT_FLINCH_PHYSICS" 1
}

$sequence "deathpose_front" "Police_animations_anims\deathpose_front.smd" {
	fps 1
	activity "ACT_DIE_FRONTSIDE" 1
}

$sequence "deathpose_back" "Police_animations_anims\deathpose_back.smd" {
	fps 1
	activity "ACT_DIE_BACKSIDE" 1
}

$sequence "deathpose_right" "Police_animations_anims\deathpose_right.smd" {
	fps 1
	activity "ACT_DIE_RIGHTSIDE" 1
}

$sequence "deathpose_left" "Police_animations_anims\deathpose_left.smd" {
	fps 1
	activity "ACT_DIE_LEFTSIDE" 1
}

$sequence "deploy" "Police_animations_anims\deploy.smd" {
	fps 30
	activity "ACT_METROPOLICE_DEPLOY_MANHACK" 1
	{ event AE_METROPOLICE_START_DEPLOY 10 "" }
	{ event AE_METROPOLICE_DEPLOY_MANHACK 33 "" }
}

$sequence "grenadethrow" "Police_animations_anims\grenadethrow.smd" {
	fps 30
	activity "ACT_COMBINE_THROW_GRENADE" 1
	{ event 7 23 "" }
}

$sequence "pistolangryidle2" "Police_animations_anims\pistolangryidle2.smd" {
	fps 4
	activity "ACT_IDLE_ANGRY_PISTOL" 1
	node "shooting_pistol"
	addlayer "pistol_Aim_all"
}

$sequence "Crouch_idle_pistol" "Police_animations_anims\Crouch_idle_pistol.smd" {
	fps 30
	activity "ACT_COVER_PISTOL_LOW" 1
	loop
	node "crouching_pistol"
}

$sequence "drawpistol" "Police_animations_anims\drawpistol.smd" {
	fps 30
	activity "ACT_METROPOLICE_DRAW_PISTOL" 1
	blendlayer "pistol_Aim_all" 0.685714 1.028571 1.028571 1.028571 spline
	{ event AE_METROPOLICE_DRAW_PISTOL 11 "" }
}

$sequence "shootp1" "Police_animations_anims\shootp1.smd" {
	fps 30
	activity "ACT_RANGE_ATTACK_PISTOL" 1
	node "shooting_pistol"
	addlayer "pistol_Aim_all"
}

$sequence "gesture_shoot_pistol" "Police_animations_anims\gesture_shoot_pistol.smd" {
	fps 30
	activity "ACT_GESTURE_RANGE_ATTACK_PISTOL" 1
	delta
}

$sequence "reload_pistol" "Police_animations_anims\reload_pistol.smd" {
	fps 30
	activity "ACT_RELOAD_PISTOL" 1
	node "shooting_pistol"
	blendlayer "pistol_Aim_all" 0 0 0 0.375 spline
	blendlayer "pistol_Aim_all" 0.75 1.025 1.025 1.025 spline
	{ event 3017 0 "" }
	{ event 3018 34 "" }
}

$sequence "crouch_reload_pistol" "Police_animations_anims\crouch_reload_pistol.smd" {
	fps 30
	activity "ACT_RELOAD_PISTOL_LOW" 1
	node "crouching_pistol"
	{ event 3017 0 "" }
	{ event 3018 56 "" }
}

$sequence "gesture_reload_pistolspine" "Police_animations_anims\gesture_reload_pistolspine.smd" {
	fps 30
	delta
	hidden
}

$sequence "gesture_reload_pistolarms" "Police_animations_anims\gesture_reload_pistolarms.smd" {
	fps 30
	hidden
}

$sequence "gesture_reload_pistol" "Police_animations_anims\gesture_reload_pistol.smd" {
	fps 30
	activity "ACT_GESTURE_RELOAD_PISTOL" 1
	node "standing_pistol"
	blendlayer "gesture_reload_pistolarms" 0 0.128205 0.820513 1.025641 spline
	blendlayer "gesture_reload_pistolspine" 0 0.128205 0.820513 1.025641 spline
	iklock "rfoot" 1 0
	iklock "lfoot" 1 0
	{ event 3017 0 "" }
	{ event 3018 37 "" }
}

$sequence "lowcover_shoot_pistol" "Police_animations_anims\lowcover_shoot_pistol.smd" {
	fps 10
	activity "ACT_RANGE_ATTACK_PISTOL_LOW" 1
	loop
	node "lowcover_pistol"
	addlayer "pistol_Aim_all"
}

$sequence "lowcover_aim_pistol" "Police_animations_anims\lowcover_aim_pistol.smd" {
	fps 30
	activity "ACT_RANGE_AIM_PISTOL_LOW" 1
	loop
	node "lowcover_pistol"
	addlayer "pistol_Aim_all"
}

$sequence "smg1angryidle1" "Police_animations_anims\smg1angryidle1.smd" {
	fps 30
	activity "ACT_IDLE_ANGRY_SMG1" 1
	loop
	node "shooting_smg"
	addlayer "SMG1_Aim_all"
}

$sequence "Crouch_idle_smg1" "Police_animations_anims\Crouch_idle_smg1.smd" {
	fps 30
	activity "ACT_COVER_SMG1_LOW" 1
	loop
	node "crouching_smg"
}

$sequence "shoot_smg1" "Police_animations_anims\shoot_smg1.smd" {
	fps 30
	activity "ACT_RANGE_ATTACK_SMG1" 1
	node "shooting_smg"
	addlayer "SMG1_Aim_all"
}

$sequence "gesture_shoot_smg1" "Police_animations_anims\gesture_shoot_smg1.smd" {
	fps 30
	activity "ACT_GESTURE_RANGE_ATTACK_SMG1" 1
	delta
}

$sequence "reload_smg1" "Police_animations_anims\reload_smg1.smd" {
	fps 30
	activity "ACT_RELOAD_SMG1" 1
	node "shooting_smg"
	addlayer "SMG1_Aim_all"
	addlayer "SMG1_Aim_all"
	{ event 3017 0 "" }
	{ event 3018 49 "" }
}

$sequence "crouch_reload_smg1" "Police_animations_anims\crouch_reload_smg1.smd" {
	fps 30
	activity "ACT_RELOAD_SMG1_LOW" 1
	node "crouching_smg"
	{ event 3017 0 "" }
	{ event 3018 52 "" }
}

$sequence "gesture_reload_smg1spine" "Police_animations_anims\gesture_reload_smg1spine.smd" {
	fps 30
	delta
	hidden
}

$sequence "gesture_reload_smg1arms" "Police_animations_anims\gesture_reload_smg1arms.smd" {
	fps 30
	hidden
}

$sequence "gesture_reload_smg1" "Police_animations_anims\gesture_reload_smg1.smd" {
	fps 30
	activity "ACT_GESTURE_RELOAD_SMG1" 1
	node "standing_smg"
	blendlayer "gesture_reload_smg1arms" 0 0.227273 0.681818 1.022727 spline
	blendlayer "gesture_reload_smg1spine" 0 0.227273 0.681818 1.022727 spline
	iklock "rfoot" 1 0
	iklock "lfoot" 1 0
	{ event 3017 0 "" }
	{ event 3018 35 "" }
}

$sequence "lowcover_shoot_smg1" "Police_animations_anims\lowcover_shoot_smg1.smd" {
	fps 30
	activity "ACT_RANGE_ATTACK_SMG1_LOW" 1
	loop
	node "lowcover_smg"
	addlayer "SMG1_Aim_all"
	{ event 3014 2 "" }
}

$sequence "lowcover_aim_smg1" "Police_animations_anims\lowcover_aim_smg1.smd" {
	fps 30
	activity "ACT_RANGE_AIM_SMG1_LOW" 1
	loop
	node "lowcover_smg"
	addlayer "SMG1_Aim_all"
}

$sequence "batonangryidle1" "Police_animations_anims\batonangryidle1.smd" {
	fps 30
	activity "ACT_IDLE_ANGRY_MELEE" 1
	loop
	node "standing_baton"
}

$sequence "swing" "Police_animations_anims\swing.smd" {
	fps 35
	activity "ACT_MELEE_ATTACK_SWING" 1
	{ event 3001 13 "" }
}

$sequence "thrust" "Police_animations_anims\thrust.smd" {
	fps 35
	activity "ACT_MELEE_ATTACK_THRUST" 1
	{ event 3001 13 "" }
}

$sequence "swinggesturespine" "Police_animations_anims\swinggesturespine.smd" {
	fps 30
	delta
	hidden
}

$sequence "swinggesturearms" "Police_animations_anims\swinggesturearms.smd" {
	fps 30
	hidden
}

$sequence "swinggesture" "Police_animations_anims\swinggesture.smd" {
	fps 35
	activity "ACT_MELEE_ATTACK_SWING_GESTURE" 1
	blendlayer "swinggesturearms" 0 0.241379 0.655172 1.034483 spline
	blendlayer "swinggesturespine" 0 0.241379 0.655172 1.034483 spline
	iklock "rfoot" 1 0
	iklock "lfoot" 1 0
	{ event 3001 13 "" }
}

$sequence "pistol_Aim_all" {
	"a_pistol_aim_straight_up"
	"a_pistol_aim_straight_up"
	"a_pistol_aim_straight_up"
	"a_pistol_aim_up_right"
	"a_pistol_aim_up_center"
	"a_pistol_aim_up_left"
	"a_pistol_aim_mid_right"
	"a_pistol_aim_mid_center"
	"a_pistol_aim_mid_left"
	"a_pistol_aim_down_right"
	"a_pistol_aim_down_center"
	"a_pistol_aim_down_left"
	fps 30
	delta
	hidden
	blendwidth 3
	blend "aim_yaw" -43.47391 45.51665
	blend "aim_pitch" -82.85746 45.59517
	iklock "rfoot" 1 0
	iklock "lfoot" 1 0
}

$sequence "WalkN_pistol_Aim_all" {
	"a_WalkN_pistol_aim_straight_up"
	"a_WalkN_pistol_aim_straight_up"
	"a_WalkN_pistol_aim_straight_up"
	"a_WalkN_pistol_aim_up_right"
	"a_WalkN_pistol_aim_up_center"
	"a_WalkN_pistol_aim_up_left"
	"a_WalkN_pistol_aim_mid_right"
	"a_WalkN_pistol_aim_mid_center"
	"a_WalkN_pistol_aim_mid_left"
	"a_WalkN_pistol_aim_down_right"
	"a_WalkN_pistol_aim_down_center"
	"a_WalkN_pistol_aim_down_left"
	fps 30
	delta
	hidden
	blendwidth 3
	blend "aim_yaw" -45.59397 44.46127
	blend "aim_pitch" -78.71045 43.57745
	iklock "rfoot" 1 0
	iklock "lfoot" 1 0
}

$sequence "SMG1_Aim_all" {
	"a_SMG1_aim_straight_up"
	"a_SMG1_aim_straight_up"
	"a_SMG1_aim_straight_up"
	"a_SMG1_aim_up_right"
	"a_SMG1_aim_up_center"
	"a_SMG1_aim_up_left"
	"a_SMG1_aim_mid_right"
	"a_SMG1_aim_mid_center"
	"a_SMG1_aim_mid_left"
	"a_SMG1_aim_down_right"
	"a_SMG1_aim_down_center"
	"a_SMG1_aim_down_left"
	fps 30
	delta
	hidden
	blendwidth 3
	blend "aim_yaw" -46.98409 48.12097
	blend "aim_pitch" -85.30637 47.80165
	iklock "rfoot" 1 0
	iklock "lfoot" 1 0
}

$sequence "WalkN_SMG1_Aim_all" {
	"a_WalkN_SMG1_aim_straight_up"
	"a_WalkN_SMG1_aim_straight_up"
	"a_WalkN_SMG1_aim_straight_up"
	"a_WalkN_SMG1_aim_up_right"
	"a_WalkN_SMG1_aim_up_center"
	"a_WalkN_SMG1_aim_up_left"
	"a_WalkN_SMG1_aim_mid_right"
	"a_WalkN_SMG1_aim_mid_center"
	"a_WalkN_SMG1_aim_mid_left"
	"a_WalkN_SMG1_aim_down_right"
	"a_WalkN_SMG1_aim_down_center"
	"a_WalkN_SMG1_aim_down_left"
	fps 30
	delta
	hidden
	blendwidth 3
	blend "aim_yaw" -50.35772 52.71159
	blend "aim_pitch" -86.32401 56.20353
	iklock "rfoot" 1 0
	iklock "lfoot" 1 0
}

$sequence "Crouch_all" {
	"a_Crouch_walkS"
	"a_Crouch_walkSE"
	"a_Crouch_walkE"
	"a_Crouch_walkNE"
	"a_Crouch_walkN"
	"a_Crouch_walkNW"
	"a_Crouch_walkW"
	"a_Crouch_walkSW"
	"a_Crouch_walkS"
	fps 30
	activity "ACT_WALK_CROUCH" 1
	loop
	blendwidth 9
	blend "move_yaw" -180 180
}

$sequence "walk_all" {
	"a_WalkS"
	"a_WalkSE"
	"a_WalkE"
	"a_WalkNE"
	"a_WalkN"
	"a_WalkNW"
	"a_WalkW"
	"a_WalkSW"
	"a_WalkS"
	fps 31
	activity "ACT_WALK" 1
	loop
	blendwidth 9
	blend "move_yaw" -180 180
	{ event 6004 9 "NPC_MetroPolice" }
	{ event 6005 25 "NPC_MetroPolice" }
}

$sequence "layer_walk_hold_baton_angry" "Police_animations_anims\layer_walk_hold_baton_angry.smd" {
	fps 30
	loop
	hidden
}

$sequence "walk_hold_baton_angry" {
	"a_WalkS"
	"a_WalkSE"
	"a_WalkE"
	"a_WalkNE"
	"a_walkN_hold_baton_angry"
	"a_WalkNW"
	"a_WalkW"
	"a_WalkSW"
	"a_WalkS"
	fps 31
	activity "ACT_WALK_ANGRY" 1
	loop
	blendwidth 9
	blend "move_yaw" -180 180
	addlayer "layer_walk_hold_baton_angry"
	{ event 6004 9 "NPC_MetroPolice" }
	{ event 6005 25 "NPC_MetroPolice" }
}

$sequence "Pistol_aim_walk_all_delta" {
	"a_walkS_pistol_aim_delta"
	"a_walkSE_pistol_aim_delta"
	"a_walkE_pistol_aim_delta"
	"a_walkNE_pistol_aim_delta"
	"a_walkN_pistol_aim_delta"
	"a_walkNW_pistol_aim_delta"
	"a_walkW_pistol_aim_delta"
	"a_walkSW_pistol_aim_delta"
	"a_walkS_pistol_aim_delta"
	fps 30
	delta
	hidden
	blendwidth 9
	blend "move_yaw" -180 180
	iklock "lfoot" 1 1
	iklock "rfoot" 1 1
}

$sequence "layer_walk_aiming_pistol" "Police_animations_anims\layer_walk_aiming_pistol.smd" {
	fps 30
	loop
	hidden
	addlayer "WalkN_pistol_Aim_all"
}

$sequence "walk_aiming_pistol_all" {
	"a_WalkS"
	"a_WalkSE"
	"a_WalkE"
	"a_WalkNE"
	"a_WalkN_aim_pistol"
	"a_WalkNW"
	"a_WalkW"
	"a_WalkSW"
	"a_WalkS"
	fps 31
	activity "ACT_WALK_AIM_PISTOL" 1
	loop
	blendwidth 9
	blend "move_yaw" -180 180
	addlayer "layer_walk_aiming_pistol"
	{ event 6004 9 "NPC_MetroPolice" }
	{ event 6005 25 "NPC_MetroPolice" }
}

$sequence "layer_walk_hold_pistol" "Police_animations_anims\layer_walk_hold_pistol.smd" {
	fps 30
	loop
	hidden
	addlayer "WalkN_pistol_Aim_all"
}

$sequence "walk_hold_pistol" {
	"a_WalkS"
	"a_WalkSE"
	"a_WalkE"
	"a_WalkNE"
	"a_walkN_hold_pistol"
	"a_WalkNW"
	"a_WalkW"
	"a_WalkSW"
	"a_WalkS"
	fps 31
	activity "ACT_WALK_PISTOL" 1
	loop
	node "standing_pistol"
	blendwidth 9
	blend "move_yaw" -180 180
	addlayer "layer_walk_hold_pistol"
	{ event 6004 9 "NPC_MetroPolice" }
	{ event 6005 25 "NPC_MetroPolice" }
}

$sequence "SMG1_aim_walk_all_delta" {
	"a_walkS_SMG1_aim_delta"
	"a_walkSE_SMG1_aim_delta"
	"a_walkE_SMG1_aim_delta"
	"a_walkNE_SMG1_aim_delta"
	"a_walkN_SMG1_aim_delta"
	"a_walkNW_SMG1_aim_delta"
	"a_walkW_SMG1_aim_delta"
	"a_walkSW_SMG1_aim_delta"
	"a_walkS_SMG1_aim_delta"
	fps 30
	delta
	hidden
	blendwidth 9
	blend "move_yaw" -180 180
	iklock "lfoot" 1 1
	iklock "rfoot" 1 1
}

$sequence "layer_walk_aiming_SMG1" "Police_animations_anims\layer_walk_aiming_SMG1.smd" {
	fps 30
	loop
	hidden
	addlayer "WalkN_SMG1_Aim_all"
}

$sequence "walk_aiming_SMG1_all" {
	"a_WalkS"
	"a_WalkSE"
	"a_WalkE"
	"a_WalkNE"
	"a_WalkN_aim_SMG1"
	"a_WalkNW"
	"a_WalkW"
	"a_WalkSW"
	"a_WalkS"
	fps 31
	activity "ACT_WALK_AIM_RIFLE" 1
	loop
	blendwidth 9
	blend "move_yaw" -180 180
	addlayer "layer_walk_aiming_SMG1"
	{ event 6004 9 "NPC_MetroPolice" }
	{ event 6005 25 "NPC_MetroPolice" }
}

$sequence "layer_walk_hold_smg1" "Police_animations_anims\layer_walk_hold_smg1.smd" {
	fps 30
	loop
	hidden
	addlayer "WalkN_SMG1_Aim_all"
}

$sequence "walk_hold_smg1" {
	"a_WalkS"
	"a_WalkSE"
	"a_WalkE"
	"a_WalkNE"
	"a_walkN_hold_smg1"
	"a_WalkNW"
	"a_WalkW"
	"a_WalkSW"
	"a_WalkS"
	fps 31
	activity "ACT_WALK_RIFLE" 1
	loop
	blendwidth 9
	blend "move_yaw" -180 180
	addlayer "layer_walk_hold_smg1"
	{ event 6004 9 "NPC_MetroPolice" }
	{ event 6005 25 "NPC_MetroPolice" }
}

$sequence "run_all" {
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
	activity "ACT_RUN" 1
	loop
	blendwidth 9
	blend "move_yaw" -180 180
	{ event 6004 7 "NPC_MetroPolice" }
	{ event 6005 16 "NPC_MetroPolice" }
}

$sequence "Pistol_aim_run_all_delta" {
	"a_runS_pistol_aim_delta"
	"a_runSE_pistol_aim_delta"
	"a_runE_pistol_aim_delta"
	"a_runNE_pistol_aim_delta"
	"a_runN_pistol_aim_delta"
	"a_runNW_pistol_aim_delta"
	"a_runW_pistol_aim_delta"
	"a_runSW_pistol_aim_delta"
	"a_runS_pistol_aim_delta"
	fps 30
	delta
	hidden
	blendwidth 9
	blend "move_yaw" -180 180
	iklock "lfoot" 1 1
	iklock "rfoot" 1 1
}

$sequence "layer_run_hold_pistol" "Police_animations_anims\layer_run_hold_pistol.smd" {
	fps 30
	loop
	hidden
	addlayer "WalkN_pistol_Aim_all"
}

$sequence "run_hold_pistol" {
	"a_RunS"
	"a_RunSE"
	"a_RunE"
	"a_RunNE"
	"a_runN_hold_pistol"
	"a_RunNW"
	"a_RunW"
	"a_RunSW"
	"a_RunS"
	fps 28
	activity "ACT_RUN_PISTOL" 1
	loop
	node "standing_pistol"
	blendwidth 9
	blend "move_yaw" -180 180
	addlayer "layer_run_hold_pistol"
	{ event 6004 7 "NPC_MetroPolice" }
	{ event 6005 16 "NPC_MetroPolice" }
}

$sequence "layer_run_aiming_pistol" "Police_animations_anims\layer_run_aiming_pistol.smd" {
	fps 30
	loop
	hidden
	addlayer "WalkN_pistol_Aim_all"
}

$sequence "run_aiming_pistol_all" {
	"a_RunS"
	"a_RunSE"
	"a_RunE"
	"a_RunNE"
	"a_runN_aim_pistol"
	"a_RunNW"
	"a_RunW"
	"a_RunSW"
	"a_RunS"
	fps 28
	activity "ACT_RUN_AIM_PISTOL" 1
	loop
	blendwidth 9
	blend "move_yaw" -180 180
	addlayer "layer_run_aiming_pistol"
	{ event 6004 7 "NPC_MetroPolice" }
	{ event 6005 16 "NPC_MetroPolice" }
}

$sequence "smg1_aim_run_all_delta" {
	"a_runS_smg1_aim_delta"
	"a_runSE_smg1_aim_delta"
	"a_runE_smg1_aim_delta"
	"a_runNE_smg1_aim_delta"
	"a_runN_smg1_aim_delta"
	"a_runNW_smg1_aim_delta"
	"a_runW_smg1_aim_delta"
	"a_runSW_smg1_aim_delta"
	"a_runS_smg1_aim_delta"
	fps 30
	delta
	hidden
	blendwidth 9
	blend "move_yaw" -180 180
	iklock "lfoot" 1 1
	iklock "rfoot" 1 1
}

$sequence "layer_run_hold_smg1" "Police_animations_anims\layer_run_hold_smg1.smd" {
	fps 30
	loop
	hidden
	addlayer "WalkN_SMG1_Aim_all"
}

$sequence "run_hold_smg1" {
	"a_RunS"
	"a_RunSE"
	"a_RunE"
	"a_RunNE"
	"a_runN_hold_smg1"
	"a_RunNW"
	"a_RunW"
	"a_RunSW"
	"a_RunS"
	fps 28
	activity "ACT_RUN_RIFLE" 1
	loop
	blendwidth 9
	blend "move_yaw" -180 180
	addlayer "layer_run_hold_smg1"
	{ event 6004 7 "NPC_MetroPolice" }
	{ event 6005 16 "NPC_MetroPolice" }
}

$sequence "layer_run_aiming_smg1" "Police_animations_anims\layer_run_aiming_smg1.smd" {
	fps 30
	loop
	hidden
	addlayer "WalkN_SMG1_Aim_all"
}

$sequence "run_aiming_smg1_all" {
	"a_RunS"
	"a_RunSE"
	"a_RunE"
	"a_RunNE"
	"a_runN_aim_smg1"
	"a_RunNW"
	"a_RunW"
	"a_RunSW"
	"a_RunS"
	fps 28
	activity "ACT_RUN_AIM_RIFLE" 1
	loop
	blendwidth 9
	blend "move_yaw" -180 180
	addlayer "layer_run_aiming_smg1"
	{ event 6004 7 "NPC_MetroPolice" }
	{ event 6005 16 "NPC_MetroPolice" }
}

$sequence "Stand_to_crouchpistol" "Police_animations_anims\Stand_to_crouchpistol.smd" {
	fps 30
	activity "ACT_TRANSITION" 1
	transition "standing_pistol" "crouching_pistol"
}

$sequence "Crouch_to_standpistol" "Police_animations_anims\Crouch_to_standpistol.smd" {
	fps 30
	activity "ACT_TRANSITION" 1
	transition "crouching_pistol" "standing_pistol"
}

$sequence "Shoot_to_crouchpistol" "Police_animations_anims\Shoot_to_crouchpistol.smd" {
	fps 30
	activity "ACT_TRANSITION" 1
	transition "shooting_pistol" "crouching_pistol"
}

$sequence "Crouch_to_shootpistol" "Police_animations_anims\Crouch_to_shootpistol.smd" {
	fps 40
	activity "ACT_TRANSITION" 1
	transition "crouching_pistol" "shooting_pistol"
	addlayer "pistolangryidle2"
}

$sequence "shoottostandpistol" "Police_animations_anims\shoottostandpistol.smd" {
	fps 30
	activity "ACT_TRANSITION" 1
	transition "shooting_pistol" "standing_pistol"
	blendlayer "pistol_Aim_all" 0 0 0 0.625 spline
}

$sequence "standtoshootpistol" "Police_animations_anims\standtoshootpistol.smd" {
	fps 30
	activity "ACT_TRANSITION" 1
	transition "standing_pistol" "shooting_pistol"
	blendlayer "pistol_Aim_all" 0 0.294118 1.058824 1.058824 spline
}

$sequence "crouch_to_lowcoverpistol" "Police_animations_anims\crouch_to_lowcoverpistol.smd" {
	fps 30
	activity "ACT_TRANSITION" 1
	transition "crouching_pistol" "lowcover_pistol"
	blendlayer "pistol_Aim_all" 0.181818 0.636364 1.045455 1.045455 spline
}

$sequence "lowcover_to_crouchpistol" "Police_animations_anims\lowcover_to_crouchpistol.smd" {
	fps 30
	activity "ACT_TRANSITION" 1
	transition "lowcover_pistol" "crouching_pistol"
	blendlayer "pistol_Aim_all" 0 0 0 0.625 spline
}

$sequence "Stand_to_crouchsmg1" "Police_animations_anims\Stand_to_crouchsmg1.smd" {
	fps 30
	activity "ACT_TRANSITION" 1
	transition "standing_smg" "crouching_smg"
	blendlayer "SMG1_Aim_all" 0 0 0 0.75 spline
}

$sequence "Crouch_to_standsmg1" "Police_animations_anims\Crouch_to_standsmg1.smd" {
	fps 30
	activity "ACT_TRANSITION" 1
	transition "crouching_smg" "standing_smg"
	blendlayer "SMG1_Aim_all" 0.181818 0.681818 1 1 spline
}

$sequence "Shoot_to_crouchsmg1" "Police_animations_anims\Shoot_to_crouchsmg1.smd" {
	fps 30
	activity "ACT_TRANSITION" 1
	transition "shooting_smg" "crouching_smg"
	blendlayer "SMG1_Aim_all" 0 0 0 0.75 spline
}

$sequence "Crouch_to_shootsmg1" "Police_animations_anims\Crouch_to_shootsmg1.smd" {
	fps 30
	activity "ACT_TRANSITION" 1
	transition "crouching_smg" "shooting_smg"
	blendlayer "SMG1_Aim_all" 0.181818 0.681818 1 1 spline
}

$sequence "crouch_to_lowcoversmg1" "Police_animations_anims\crouch_to_lowcoversmg1.smd" {
	fps 30
	activity "ACT_TRANSITION" 1
	transition "crouching_smg" "lowcover_smg"
	blendlayer "SMG1_Aim_all" 0 0.555556 1 1 spline
}

$sequence "lowcover_to_crouchsmg1" "Police_animations_anims\lowcover_to_crouchsmg1.smd" {
	fps 30
	activity "ACT_TRANSITION" 1
	transition "lowcover_smg" "crouching_smg"
	blendlayer "SMG1_Aim_all" 0 0 0 0.555556 spline
}

$sequence "turnleft" "Police_animations_anims\turnleft.smd" {
	fps 20
	activity "ACT_GESTURE_TURN_LEFT" 1
}

$sequence "turnright" "Police_animations_anims\turnright.smd" {
	fps 20
	activity "ACT_GESTURE_TURN_RIGHT" 1
}

$sequence "gesture_turn_left_45default" "Police_animations_anims\gesture_turn_left_45default.smd" {
	fps 30
	delta
	hidden
}

$sequence "gesture_turn_left_45inDelta" "Police_animations_anims\gesture_turn_left_45inDelta.smd" {
	fps 30
	delta
	hidden
}

$sequence "gesture_turn_left_45outDelta" "Police_animations_anims\gesture_turn_left_45outDelta.smd" {
	fps 30
	delta
	hidden
}

$sequence "gesture_turn_left_45" "Police_animations_anims\gesture_turn_left_45.smd" {
	fps 60
	activity "ACT_GESTURE_TURN_LEFT45" 1
	addlayer "gesture_turn_left_45default"
	blendlayer "gesture_turn_left_45default" 0.408163 0.408163 0.408163 1.020408 spline
	addlayer "gesture_turn_left_45inDelta"
	blendlayer "gesture_turn_left_45outDelta" 0.408163 0.408163 0.408163 1.020408 spline
}

$sequence "gesture_turn_left_90default" "Police_animations_anims\gesture_turn_left_90default.smd" {
	fps 30
	delta
	hidden
}

$sequence "gesture_turn_left_90inDelta" "Police_animations_anims\gesture_turn_left_90inDelta.smd" {
	fps 30
	delta
	hidden
}

$sequence "gesture_turn_left_90outDelta" "Police_animations_anims\gesture_turn_left_90outDelta.smd" {
	fps 30
	delta
	hidden
}

$sequence "gesture_turn_left_90" "Police_animations_anims\gesture_turn_left_90.smd" {
	fps 60
	activity "ACT_GESTURE_TURN_LEFT90" 1
	addlayer "gesture_turn_left_90default"
	blendlayer "gesture_turn_left_90default" 0.357143 0.357143 0.357143 1.017857 spline
	addlayer "gesture_turn_left_90inDelta"
	blendlayer "gesture_turn_left_90outDelta" 0.357143 0.357143 0.357143 1.017857 spline
}

$sequence "gesture_turn_right_45default" "Police_animations_anims\gesture_turn_right_45default.smd" {
	fps 30
	delta
	hidden
}

$sequence "gesture_turn_right_45inDelta" "Police_animations_anims\gesture_turn_right_45inDelta.smd" {
	fps 30
	delta
	hidden
}

$sequence "gesture_turn_right_45outDelta" "Police_animations_anims\gesture_turn_right_45outDelta.smd" {
	fps 30
	delta
	hidden
}

$sequence "gesture_turn_right_45" "Police_animations_anims\gesture_turn_right_45.smd" {
	fps 60
	activity "ACT_GESTURE_TURN_RIGHT45" 1
	addlayer "gesture_turn_right_45default"
	blendlayer "gesture_turn_right_45default" 0.408163 0.408163 0.408163 1.020408 spline
	addlayer "gesture_turn_right_45inDelta"
	blendlayer "gesture_turn_right_45outDelta" 0.408163 0.408163 0.408163 1.020408 spline
}

$sequence "gesture_turn_right_90default" "Police_animations_anims\gesture_turn_right_90default.smd" {
	fps 30
	delta
	hidden
}

$sequence "gesture_turn_right_90inDelta" "Police_animations_anims\gesture_turn_right_90inDelta.smd" {
	fps 30
	delta
	hidden
}

$sequence "gesture_turn_right_90outDelta" "Police_animations_anims\gesture_turn_right_90outDelta.smd" {
	fps 30
	delta
	hidden
}

$sequence "gesture_turn_right_90" "Police_animations_anims\gesture_turn_right_90.smd" {
	fps 60
	activity "ACT_GESTURE_TURN_RIGHT90" 1
	addlayer "gesture_turn_right_90default"
	blendlayer "gesture_turn_right_90default" 0.408163 0.408163 0.408163 1.020408 spline
	addlayer "gesture_turn_right_90inDelta"
	blendlayer "gesture_turn_right_90outDelta" 0.408163 0.408163 0.408163 1.020408 spline
}

$sequence "jump_holding_jump" "Police_animations_anims\jump_holding_jump.smd" {
	fps 30
	activity "ACT_JUMP" 1
}

$sequence "jump_holding_glide" "Police_animations_anims\jump_holding_glide.smd" {
	fps 5
	activity "ACT_GLIDE" 1
}

$sequence "jump_holding_land" "Police_animations_anims\jump_holding_land.smd" {
	fps 45
	activity "ACT_LAND" 1
	fadein 0.15
}

$sequence "Neutral_to_Choked_Barnacle" "Police_animations_anims\Neutral_to_Choked_Barnacle.smd" {
	fps 30
}

$sequence "Choked_Barnacle" "Police_animations_anims\Choked_Barnacle.smd" {
	fps 30
	loop
}

$sequence "Crushed_Barnacle" "Police_animations_anims\Crushed_Barnacle.smd" {
	fps 30
}

$sequence "Dropship_Deploy" "Police_animations_anims\Dropship_Deploy.smd" {
	fps 30
}

$sequence "Man_Gun_Aim_all" {
	"Man_Gun_up_right"
	"Man_Gun_up_center"
	"Man_Gun_up_left"
	"Man_Gun_mid_right"
	"Man_Gun_mid_center"
	"Man_Gun_mid_left"
	"Man_Gun_down_right"
	"Man_Gun_down_center"
	"Man_Gun_down_left"
	fps 30
	delta
	hidden
	blend "aim_yaw" -60 60
	blend "aim_pitch" -35 50
	iklock "lfoot" 1 0
}

$sequence "Man_Gun" "Police_animations_anims\Man_Gun.smd" {
	fps 30
	activity "ACT_IDLE_MANNEDGUN" 1
	loop
	addlayer "Man_Gun_Aim_all"
}

$ikchain "rhand" "ValveBiped.Bip01_R_Hand" knee 0.707 0.707 0
$ikchain "lhand" "ValveBiped.Bip01_L_Hand" knee 0.707 0.707 0
$ikchain "rfoot" "ValveBiped.Bip01_R_Foot" knee 0.707 -0.707 0
$ikchain "lfoot" "ValveBiped.Bip01_L_Foot" knee 0.707 -0.707 0

$ikautoplaylock "rfoot" 1 0.1
$ikautoplaylock "lfoot" 1 0.1
$ikautoplaylock "rfoot" 1 0.1
$ikautoplaylock "lfoot" 1 0.1

$bonesaveframe "ValveBiped.Bip01_Pelvis" position rotation
$bonesaveframe "ValveBiped.Bip01_Spine" rotation
$bonesaveframe "ValveBiped.Bip01_Spine1" rotation
$bonesaveframe "ValveBiped.Bip01_Spine2" rotation
$bonesaveframe "ValveBiped.Bip01_Spine4" rotation
$bonesaveframe "ValveBiped.Bip01_Neck1" rotation
$bonesaveframe "ValveBiped.Bip01_Head1" rotation
$bonesaveframe "ValveBiped.Bip01_R_Clavicle" rotation
$bonesaveframe "ValveBiped.Bip01_R_UpperArm" rotation
$bonesaveframe "ValveBiped.Bip01_R_Forearm" rotation
$bonesaveframe "ValveBiped.Bip01_R_Hand" rotation
$bonesaveframe "ValveBiped.Bip01_L_Clavicle" rotation
$bonesaveframe "ValveBiped.Bip01_L_UpperArm" rotation
$bonesaveframe "ValveBiped.Bip01_L_Forearm" rotation
$bonesaveframe "ValveBiped.Bip01_L_Hand" rotation
$bonesaveframe "ValveBiped.Bip01_R_Thigh" rotation
$bonesaveframe "ValveBiped.Bip01_R_Calf" rotation
$bonesaveframe "ValveBiped.Bip01_R_Foot" rotation
$bonesaveframe "ValveBiped.Bip01_L_Thigh" rotation
$bonesaveframe "ValveBiped.Bip01_L_Calf" rotation
$bonesaveframe "ValveBiped.Bip01_L_Foot" rotation

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

