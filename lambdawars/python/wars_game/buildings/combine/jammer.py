from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass
from .basepowered import PoweredBuildingInfo, BaseFactoryPoweredBuilding
from entities import entity 
from particles import PATTACH_POINT_FOLLOW

if isserver:
    from particles import PrecacheParticleSystem

@entity('build_comb_jammer', networked=True)
class CombineJammer(BaseFactoryPoweredBuilding, BaseClass):
    def __init__(self):
        super().__init__()
        
        self.idlefx = [["pg_jammer_idle","p0",None],["pg_jammer_idle","p1",None],["pg_jammer_idle","p2",None]]

    if isserver:
        def Precache(self):
            super(CombineJammer, self).Precache()
            
            PrecacheParticleSystem( "pg_jammer_idle" )
            PrecacheParticleSystem( "pg_blue_flash" )

    else:
        def OnConstructed(self):
            super().OnConstructed()
            
            self.CreateIdleEffect()

        def UpdateOnRemove(self):
            super().UpdateOnRemove()
            
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

        def OnBuildStateChanged(self):
            super(CombineJammer, self).OnBuildStateChanged()
            
            if self.isproducing:
                self.StartWorkParticals()
            else:
                self.StopWorkParticals()
                
        def UpdateOnRemove(self):
            super(CombineJammer, self).UpdateOnRemove()
            
            self.StopWorkParticals()
            self.StopIdleEffect()

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

    workparticalsfx = None
    
# Register unit
class JammerInfo(PoweredBuildingInfo):
    name = 'build_comb_jammer' 
    displayname = '#BuildCombJammer_Name'
    description = '#BuildCombJammer_Description'
    cls_name = 'build_comb_jammer'
    image_name = 'vgui/combine/buildings/build_comb_armory'
    modelname = 'models/pg_props/pg_buildings/combine/pg_combine_jammer.mdl'
    #explodemodel = 'models/pg_props/pg_buildings/combine/pg_combine_armory_des.mdl'
    explodemodel_lightingoffset = Vector(0, 0, 250)
    idleactivity = 'ACT_IDLE'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    workactivity = 'ACT_WORK'
    #zoffset = -8.0
    techrequirements = ['build_comb_garrison']
    costs = [('requisition', 40), ('power', 20)]
    health = 200
    buildtime = 20.0
    abilities = {
        0 : 'grenade_unlock',
        8 : 'cancel',
    } 
    sound_select = 'build_comb_armory'
    sound_death = 'build_comb_armory_destroy'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (1, 10, 1, 128) # Amplitude, frequence, duration, radius