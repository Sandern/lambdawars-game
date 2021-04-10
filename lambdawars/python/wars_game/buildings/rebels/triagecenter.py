from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass
from entities import entity
from particles import PATTACH_POINT_FOLLOW
from core.abilities import SubMenu

if isserver:
    from particles import PrecacheParticleSystem

@entity('build_reb_triagecenter', networked=True)
class RebelsTriageCenter(BaseClass):
    if isclient:
        def OnBuildStateChanged(self):
            super().OnBuildStateChanged()
            
            if self.isproducing:
                self.StartChimneySmoke()
            else:
                self.StopChimneySmoke()
                
        def UpdateOnRemove(self):
            super().UpdateOnRemove()
            
            self.StopChimneySmoke()
            
        def ExplodeHandler(self, event):
            self.StopChimneySmoke()
            super().ExplodeHandler(event)

        def StartChimneySmoke(self):
            if self.chimneyfx:
                return
            self.chimneyfx = self.ParticleProp().Create("pg_smoke02", PATTACH_POINT_FOLLOW, 'smoke01')
            
        def StopChimneySmoke(self):
            if not self.chimneyfx:
                return
            self.ParticleProp().StopEmission(self.chimneyfx)
            self.chimneyfx = None
            
    else:
        def Precache(self):
            super().Precache()
            
            PrecacheParticleSystem("pg_smoke02")

    # Settings
    autoconstruct = False
    buildtarget = Vector(0, -280, 32)
    buildangle = QAngle(0, 0, 0)
    rallylineenabled = False
    customeyeoffset = Vector(0,0,90)

    chimneyfx = None
    
# Register unit
class TriageCenterInfo(WarsBuildingInfo):
    name        = "build_reb_triagecenter" 
    displayname = "#BuildRebTriCent_Name"
    description = "#BuildRebTriCent_Description"
    cls_name    = "build_reb_triagecenter"
    image_name  = 'vgui/rebels/buildings/build_reb_triagecenter'
    modelname = 'models/pg_props/pg_buildings/rebels/pg_rebel_med_center.mdl'
    explodemodel = 'models/pg_props/pg_buildings/rebels/pg_rebel_med_center_destruction.mdl'
    costs = [('requisition', 25), ('scrap', 25)]
    health = 600
    buildtime = 31.0
    techrequirements = ['build_reb_barracks']
    abilities   = {
        0 : 'medic_healrate_upgrade',
        1 : 'medic_regenerate_upgrade',
        2 : 'medic_maxenergy_upgrade',
        3 : 'medic_smg1_upgrade',
        8 : 'cancel',
    }
    idleactivity = 'ACT_IDLE'
    # workactivity = 'ACT_WORK'
    explodeactivity = 'ACT_EXPLODE'
    scale = 0.85
    constructionactivity = 'ACT_CONSTRUCTION'
    sound_work = 'rebel_triage_working'
    sound_select = 'build_reb_triagecenter'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_aid'])

class DestroyHQTriageCenterInfo(TriageCenterInfo):
    name        = "build_reb_triagecenter_destroyhq"
    techrequirements = ['build_reb_barracks_destroyhq']