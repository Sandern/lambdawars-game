from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseBuilding as BaseClass
from entities import entity
from particles import PATTACH_POINT_FOLLOW

if isserver:
    from particles import PrecacheParticleSystem
    from core.units import UnitCombatSense

@entity('build_reb_radiotower', networked=True)
class RebelsRadioTower(BaseClass):
    if isclient:
        def OnBuildStateChanged(self):
            super(RebelsRadioTower, self).OnBuildStateChanged()
            
            if self.isproducing:
                self.StartChimneySmoke()
            else:
                self.StopChimneySmoke()
                
        def UpdateOnRemove(self):
            super(RebelsRadioTower, self).UpdateOnRemove()
            
            self.StopChimneySmoke()

        def StartChimneySmoke(self):
            if self.chimneyfx:
                return
            self.chimneyfx = self.ParticleProp().Create("pg_blue_flash", PATTACH_POINT_FOLLOW, 'antena1')
            
        def StopChimneySmoke(self):
            if not self.chimneyfx:
                return
            self.ParticleProp().StopEmission(self.chimneyfx)
            self.chimneyfx = None
            
    else:
        def Precache(self):
            super(RebelsRadioTower, self).Precache()
            
            PrecacheParticleSystem( "pg_blue_flash" )

    # Settings     
    autoconstruct = False
    #customeyeoffset = Vector(0,0,150)
    
    chimneyfx = None

# Register unit
class RebelRadioTowerInfo(WarsBuildingInfo):
    name        = "build_reb_radiotower"
    displayname = '#BuildRebRadioTower_Name'
    description = '#BuildRebRadioTower_Description'
    cls_name    = "build_reb_radiotower"
    image_name  = 'vgui/rebels/buildings/build_reb_radiotower'
    modelname = 'models/pg_props/pg_buildings/pg_rebel_radio_tower.mdl'
    explodemodel = 'models/pg_props/pg_buildings/pg_rebel_radio_tower_des.mdl'
    explodemodel_lightingoffset = Vector(0, 0, 100)
    idleactivity = 'ACT_IDLE'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    workactivity = 'ACT_WORK'
    zoffset = 0.0
    techrequirements = ['build_reb_hq']
    costs = [('requisition', 50)]
    health = 600
    buildtime = 450.0
    abilities   = {
        8 : 'cancel',
    }
    sound_select = 'build_reb_radiotower'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    # sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_barracks'])
    requirerotation = False
    
@entity('build_reb_detectiontower')
class RebelsDetectionTower(RebelsRadioTower):
    def __init__(self):
        super(RebelsDetectionTower, self).__init__()

        if isserver:
            self.senses = UnitCombatSense(self)
            
    def UpdateOnRemove(self):
        # ALWAYS CHAIN BACK!
        super(RebelsDetectionTower, self).UpdateOnRemove()

        self.senses = None
        
    if isserver:
        def OnUnitTypeChanged(self, oldunittype):
            super(RebelsDetectionTower, self).OnUnitTypeChanged(oldunittype)
            
            self.UpdateSensingDistance()
    
        def UpdateSensingDistance(self):
            if self.senses:
                if self.unitinfo.sensedistance != -1:
                    self.senses.sensedistance = self.unitinfo.sensedistance
                else:
                    self.senses.sensedistance = self.unitinfo.viewdistance

        def BuildThink(self):
            self.senses.PerformSensing()
            
            super(RebelsDetectionTower, self).BuildThink()
            
    senses = None
    detector = True
    
class RebelScanTowerInfo(RebelRadioTowerInfo):
    name = "build_reb_detectiontower"
    cls_name = 'build_reb_detectiontower'
    costs = [('requisition', 20), ('scrap', 30)]
    techrequirements = ['build_reb_barracks']
    unitenergy = 100
    unitenergy_initial = 50
    buildtime = 32.0
    sensedistance = 256.0
    viewdistance = 1280
    abilities   = {
        0 : 'scan',
        8 : 'cancel',
    }
    
class DestroyHQRebelScanTowerInfo(RebelScanTowerInfo):
    name = "build_reb_detectiontower_destroyhq"
    techrequirements = ['build_reb_barracks_destroyhq']