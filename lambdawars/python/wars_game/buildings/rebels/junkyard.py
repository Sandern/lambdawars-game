from vmath import Vector, QAngle
import math
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass, constructedlistpertype
from entities import entity
from particles import PATTACH_POINT_FOLLOW

if isserver:
    from particles import PrecacheParticleSystem
    
@entity('build_reb_junkyard', networked=True)
class RebelsJunkyard(BaseClass):

    def UpdateClientBuildProgress(self, building):
        weight = self.GetBuildProgress()
        t = ((weight*100.0)%1.0)
        a = math.floor(((weight*100)%10))
        building.SetPoseParameter('progressA', a+(t**2))

        building.SetPoseParameter('progressB', ((weight*10.0)%10.0))

        t = ((weight)%1.0)
        a = math.floor(((weight)%10))
        building.SetPoseParameter('progressC', a+(t**2))
            
        self.SetNextClientThink(gpGlobals.curtime) 

        
    if isclient:
        def OnBuildStateChanged(self):
            super(RebelsJunkyard, self).OnBuildStateChanged()
            
            if self.isproducing:
                self.StartSmoke()
            else:
                self.StopSmoke()
        
        def StartSmoke(self):
            if not self.smokefx:
                self.smokefx = self.ParticleProp().Create("pg_chimney_small", PATTACH_POINT_FOLLOW, 'chimney')
            if not self.smokefx2:
                self.smokefx2 = self.ParticleProp().Create("pg_junkyard_work", PATTACH_POINT_FOLLOW, 'hut_exit')
            
        def StopSmoke(self):
            if self.smokefx:
                self.ParticleProp().StopEmission(self.smokefx)
                self.smokefx = None
            if self.smokefx2:
                self.ParticleProp().StopEmission(self.smokefx2)
                self.smokefx2 = None   
    else:
        def Precache(self):
            super(RebelsJunkyard, self).Precache()
            
            PrecacheParticleSystem( "pg_chimney_small" )
            PrecacheParticleSystem( "pg_junkyard_work" )
            
            
    # Settings
    autoconstruct = False
    smokefx = None
    smokefx2 = None
    buildtarget = Vector(0, -280, 32)
    buildangle = QAngle(0, 0, 0)
    customeyeoffset = Vector(0,0,90)
    
# Register unit
class JunkyardInfo(WarsBuildingInfo):
    name        = "build_reb_junkyard" 
    displayname = "#Reb_Junkyard_Name"
    description = "#Reb_Junkyard_Description"
    cls_name    = "build_reb_junkyard"
    image_name  = 'vgui/rebels/buildings/build_reb_junkyard'
    modelname = 'models/pg_props/pg_buildings/rebels/pg_junkyard.mdl'
    explodemodel = 'models/pg_props/pg_buildings/rebels/pg_junkyard_des.mdl'
    costs = [('requisition', 20)]
    resource_category = 'economy'
    health = 350
    buildtime = 25.0
    generateresources = {'type' : 'scrap', 'amount' : 1.0, 'interval' : 10.0} #so a junkyard can generate some scrap.
    techrequirements = ['build_reb_hq']
    abilities   = {
        0 : 'unit_rebel_engineer',
        1 : 'unit_dog',
        8 : 'cancel',
    } 
    idleactivity = 'ACT_IDLE'
    explodeactivity = 'ACT_EXPLODE'
    workactivity = 'ACT_WORK'
    constructionactivity = 'ACT_CONSTRUCTION'
    sound_work = 'rebel_junkyard_working'
    sound_select = 'build_reb_junkyard'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'pg_rebel_junkyard_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_junkyard','sai_scrap_collection'])
    placerestrictions = [
        {'unittype' : 'scrap_marker', 'radius' : 180.0},
        {'unittype' : 'scrap_marker_small', 'radius' : 180.0},
    ]

class DestroyHQJunkyardInfo(JunkyardInfo):
    name        = "build_reb_junkyard_destroyhq"
    techrequirements = ['build_reb_hq_destroyhq']
    abilities   = {
        0 : 'destroyhq_unit_rebel_engineer',
        1: 'destroyhq_unit_dog',
        8 : 'cancel',
    }

class TutorialJunkyardInfo(JunkyardInfo):
    name        = "build_reb_junkyard_tutorial"
    techrequirements = ['build_reb_hq_tutorial']
    abilities   = {
        0 : 'tutorial_rebel_engineer',
        8 : 'cancel',
    }