from wars_game.buildings.baseregeneration import BaseRegeneration
from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo
from entities import entity
from particles import PATTACH_POINT_FOLLOW
from fields import BooleanField

if isserver:
    from particles import PrecacheParticleSystem

@entity('build_comb_regenerationpost', networked=True)
class CombineRegenerationPost(BaseRegeneration):
    def __init__(self):
        super().__init__()
        
        self.idlefx = [["pg_jammer_idle","p0",None],["pg_jammer_idle","p1",None],["pg_jammer_idle","p2",None]]

    if isserver:
        def Precache(self):
            super().Precache()
            
            PrecacheParticleSystem("pg_jammer_idle")
            PrecacheParticleSystem("pg_blue_flash")

        def BuildThink(self):
            super().BuildThink()

            if self.healarea:
                self.ishealing = self.healarea.healing
    else:
        def OnConstructed(self):
            super().OnConstructed()
            
            self.CreateIdleEffect()

        def UpdateOnRemove(self):
            super().UpdateOnRemove()

            self.StopWorkParticals()
            self.StopIdleEffect()

        def ExplodeHandler(self, event):
            self.StopIdleEffect()
            super().ExplodeHandler(event)

        def CreateIdleEffect(self):
            for x in self.idlefx:
                if not x[2]:
                    x[2] = self.ParticleProp().Create(x[0], PATTACH_POINT_FOLLOW, x[1])
                x[2].SetControlPoint(2, self.GetTeamColor())

        def StopIdleEffect(self):
            for x in self.idlefx:
                if x[2]:
                    self.ParticleProp().StopEmission(x[2])
                x[2] = None

        def OnIsHealingChanged(self):
            if self.ishealing:
                self.StartWorkParticals()
            else:
                self.StopWorkParticals()

        def StartWorkParticals(self):
            if self.workparticalsfx:
                return
            self.workparticalsfx = self.ParticleProp().Create("pg_blue_flash", PATTACH_POINT_FOLLOW, 'light')
            
        def StopWorkParticals(self):
            if not self.workparticalsfx:
                return
            self.ParticleProp().StopEmission(self.workparticalsfx)
            self.workparticalsfx = None

    # Settings
    autoconstruct = False
    buildtarget = Vector(0, -210, 32)
    buildangle = QAngle(0, 0, 0)
    #customeyeoffset = Vector(0,0,150)
    rallylineenabled = False

    ishealing = BooleanField(value=False, networked=True, clientchangecallback='OnIsHealingChanged')
    workparticalsfx = None

class CombineRegenerationPostInfo(WarsBuildingInfo):
    name = "build_comb_regenerationpost"
    displayname = "#BuildCombMedStation_Name"
    description = "#BuildCombMedStation_Description"
    cls_name = "build_comb_regenerationpost"
    image_name  = "vgui/combine/buildings/build_comb_regenerationpost.vmt"
    image_dis_name = "vgui/combine/buildings/build_comb_regenerationpost.vmt"
    modelname = 'models/pg_props/pg_buildings/combine/pg_combine_jammer.mdl'
    explodemodel = 'models/pg_props/pg_buildings/combine/pg_combine_jammer_des.mdl'
    explodemodel_lightingoffset = Vector(0, 0, 250)
    idleactivity = 'ACT_IDLE'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    workactivity = 'ACT_WORK'
    health = 250
    buildtime = 25.0
    placemaxrange = 96.0
    #placeatmins = True
    costs = [[('requisition', 25), ('power', 10)], [('kills', 5)]]
    techrequirements = ['build_comb_armory']
    viewdistance = 640
    abilities   = {
        8 : 'cancel',
    } 
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_aid'])
    requirerotation = False


@entity('build_char_comb_regenerationpost', networked=True)
class CombineRegenerationPostChar(BaseRegeneration):
    def __init__(self):
        super().__init__()

        self.idlefx = [["pg_jammer_idle", "p0", None], ["pg_jammer_idle", "p1", None], ["pg_jammer_idle", "p2", None]]

    if isserver:
        def Precache(self):
            super().Precache()

            PrecacheParticleSystem("pg_jammer_idle")
            PrecacheParticleSystem("pg_blue_flash")

        def BuildThink(self):
            super().BuildThink()

            if self.healarea:
                self.ishealing = self.healarea.healing
    else:
        def OnConstructed(self):
            super().OnConstructed()

            self.CreateIdleEffect()

        def UpdateOnRemove(self):
            super().UpdateOnRemove()

            self.StopWorkParticals()
            self.StopIdleEffect()

        def ExplodeHandler(self, event):
            self.StopIdleEffect()
            super().ExplodeHandler(event)

        def CreateIdleEffect(self):
            for x in self.idlefx:
                if not x[2]:
                    x[2] = self.ParticleProp().Create(x[0], PATTACH_POINT_FOLLOW, x[1])
                x[2].SetControlPoint(2, self.GetTeamColor())

        def StopIdleEffect(self):
            for x in self.idlefx:
                if x[2]:
                    self.ParticleProp().StopEmission(x[2])
                x[2] = None

        def OnIsHealingChanged(self):
            if self.ishealing:
                self.StartWorkParticals()
            else:
                self.StopWorkParticals()

        def StartWorkParticals(self):
            if self.workparticalsfx:
                return
            self.workparticalsfx = self.ParticleProp().Create("pg_blue_flash", PATTACH_POINT_FOLLOW, 'light')

        def StopWorkParticals(self):
            if not self.workparticalsfx:
                return
            self.ParticleProp().StopEmission(self.workparticalsfx)
            self.workparticalsfx = None

    # Settings
    autoconstruct = True
    buildtarget = Vector(0, -210, 32)
    buildangle = QAngle(0, 0, 0)
    # customeyeoffset = Vector(0,0,150)
    rallylineenabled = False

    ishealing = BooleanField(value=False, networked=True, clientchangecallback='OnIsHealingChanged')
    workparticalsfx = None

class CombineRegenerationPostCharInfo(CombineRegenerationPostInfo):
    name = 'build_char_comb_regenerationpost'
    cls_name = 'build_char_comb_regenerationpost'
    costs = []
    techrequirements = []
    rechargetime = 60.0
    health = 200
    buildtime = 20.0
    viewdistance = 256

class OverrunCombineRegenerationPostInfo(CombineRegenerationPostInfo):
    name = 'overrun_build_comb_regenerationpost'
    techrequirements = ['or_tier2_research']
    costs = [('kills', 15)]
    hidden = True