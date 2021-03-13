from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass
from entities import entity 
from particles import PATTACH_POINT_FOLLOW
from core.abilities import SubMenu

if isserver:
    from particles import PrecacheParticleSystem

@entity('build_reb_specialops', networked=True)
class RebelsSpecialOps(BaseClass):
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
    buildtarget = Vector(0, -210, 32)
    buildangle = QAngle(0, 0, 0)
    customeyeoffset = Vector(0,0,60)

    chimneyfx = None
    
# Register unit
class SpecialOpsInfo(WarsBuildingInfo):
    name        = "build_reb_specialops" 
    displayname = "#BuildRebSpecialOps_Name"
    description = "#BuildRebSpecialOps_Description"
    cls_name    = "build_reb_specialops"
    image_name  = 'vgui/rebels/buildings/build_reb_specialops'
    modelname = 'models/pg_props/pg_buildings/rebels/pg_rebel_specops.mdl'
    explodemodel = 'models/pg_props/pg_buildings/rebels/pg_rebel_specops_destruction.mdl'
    techrequirements = ['build_reb_munitiondepot']
    costs = [('requisition', 50), ('scrap', 75)]
    health = 800
    buildtime = 88.0
    scale = 0.90
    abilities   = {
		0 : 'unit_rebel_rpg',
		1 : 'unit_rebel_flamer',
		2 : 'unit_rebel_heavy',
		3 : 'unit_rebel_tau',
		4 : 'unit_rebel_saboteur',
		8 : 'cancel',
    }
    idleactivity = 'ACT_IDLE'
    # workactivity = 'ACT_WORK'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    sound_select = 'build_reb_specialops'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_barracks', 'sai_building_specops'])
	
class DestroyHQSpecialOpsInfo(SpecialOpsInfo):
    name        = "build_reb_specialops_destroyhq"
    techrequirements = ['build_reb_munitiondepot_destroyhq']