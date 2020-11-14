"""
A building that launches headcrab canisters at target positions.
"""

from vmath import Vector, QAngle
from core.buildings import UnitBaseBuilding as BaseClass
from .basepowered import PoweredBuildingInfo, BasePoweredBuilding
from entities import entity
from particles import PATTACH_POINT_FOLLOW
from fields import BooleanField

if isserver:
    from particles import PrecacheParticleSystem

@entity('build_comb_headcrabcanisterlauncher', networked=True)
class CombineHeadcrabCanisterLauncher(BasePoweredBuilding, BaseClass):
    def UpdateBuildingActivity(self):
        if self.launching:
            info = self.unitinfo
            if info.workactivity:
                self.ChangeToActivity(info.workactivity)
                return
        super().UpdateBuildingActivity()
        
    def OnLaunchingChanged(self):
        self.UpdateBuildingActivity()
        
    def DoLaunchAnimation(self, launchendtime=2.0):
        self.launching = True
        self.SetThink(self.LaunchEndThink, gpGlobals.curtime + launchendtime)
        
    def LaunchEndThink(self):
        self.launching = False

    if isclient:
        def OnBuildStateChanged(self):
            super().OnBuildStateChanged()
            
            if self.isproducing:
                self.StartWorkParticals()
            else:
                self.StopWorkParticals()
                
        def UpdateOnRemove(self):
            super().UpdateOnRemove()
            
            self.StopWorkParticals()

        def StartWorkParticals(self):
            if self.workparticalsfx:
                return
            self.workparticalsfx = self.ParticleProp().Create("pg_light_cylinder", PATTACH_POINT_FOLLOW, 'light_a01')
            self.workparticalsfx2 = self.ParticleProp().Create("pg_light_cylinder", PATTACH_POINT_FOLLOW, 'light_a02')
            self.workparticalsfx3 = self.ParticleProp().Create("pg_light_cylinder", PATTACH_POINT_FOLLOW, 'light_a03')
            
        def StopWorkParticals(self):
            if not self.workparticalsfx:
                return
            self.ParticleProp().StopEmission(self.workparticalsfx)
            self.ParticleProp().StopEmission(self.workparticalsfx2)
            self.ParticleProp().StopEmission(self.workparticalsfx3)
            self.workparticalsfx = None
            self.workparticalsfx2 = None
            self.workparticalsfx3 = None
            
    else:
        def Precache(self):
            super().Precache()
            
            PrecacheParticleSystem( "pg_light_cylinder" )
    
    def FindPositionForUnit(self, unitinfo):
        return self.buildtargetabs
        
    # Settings
    autoconstruct = False
    buildtarget = Vector(0, 0, 64)
    buildangle = QAngle(0, 0, 0) 

    workparticalsfx = None
    workparticalsfx2 = None
    workparticalsfx3 = None
    
    launching = BooleanField(value=False, networked=True, clientchangecallback='OnLaunchingChanged')

class HeadcrabCanisterLauncherInfo(PoweredBuildingInfo):
    name = "build_comb_headcrabcanisterlauncher" 
    displayname = "#BuildCombHCCLauncher_Name"
    description = "#BuildCombHCCLauncher_Description"
    cls_name = "build_comb_headcrabcanisterlauncher"
    image_name = "vgui/combine/buildings/build_comb_canisterlauncher.vmt"
    image_dis_name = 'vgui/combine/buildings/build_comb_canisterlauncher.vmt'
    modelname = 'models/structures/combine/canisterlauncher.mdl'
    idleactivity = 'ACT_IDLE'
    constructionactivity = 'ACT_CONSTRUCTION'
    workactivity = 'ACT_WORK'
    explodeactivity = 'ACT_EXPLODE'
    techrequirements = ['build_comb_armory']
    costs = [('requisition', 40), ('power', 65)]
    health = 400
    buildtime = 30.0
    scale = 1.0
    abilities = {
        0: 'launch_headcrabcanister',
        1: 'launch_headcrabcanister_fasttype',
        2: 'launch_headcrabcanister_poisontype',
        3: 'launch_headcrabcanister_emptytype',
        8: 'cancel',
    } 
    sound_select = 'build_comb_headcrabcanisterlauncher'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = PoweredBuildingInfo.sai_hint
    requirerotation = False
