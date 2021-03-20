from vmath import Vector
from core.buildings import WarsBuildingInfo
from core.buildings import UnitBaseGarrisonableBuilding as BaseClass, GarrisonableBuildingInfo
from entities import entity

@entity('build_rebelregeneration', networked=True)
class RebelsAidStation(BaseClass):
    maxpopulation = 8
    playerowned = True
    autoconstruct = False
    
    def BuildThink(self):
        dt = gpGlobals.curtime - self.GetLastThink()
        heal = int(round(dt * self.healrate))
    
        for unit in self.units:
            # Must not be mechanic
            if 'mechanic' in unit.attributes:
                continue
                
            if unit.health < unit.maxhealth:
                unit.health += min(heal, (unit.maxhealth-unit.health))
    
        super().BuildThink()
        
    healrate = 6
    
class RebelsAidStationInfo(GarrisonableBuildingInfo):
    name = "build_reb_aidstation"
    displayname = "#BuildRebAidStation_Name"
    description = "#BuildRebAidStation_Description"
    cls_name = "build_rebelregeneration"
    image_name = 'vgui/rebels/buildings/build_reb_aidstation'
    modelname = 'models/structures/resistance/aidstation.mdl'
    health = 500
    buildtime = 25.0
    placemaxrange = 260.0
    costs = [[('requisition', 40), ('scrap', 10)], [('kills', 5)]]
    techrequirements = ['build_reb_triagecenter']
    attributes = ['defence']
    abilities   = {
        0 : 'ungarrisonall',
        1 : 'onhealedexit',
        8 : 'cancel',
    } 
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    #sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_aid'])
	
class DestroyHQRebelsAidStationInfo(RebelsAidStationInfo):
    name = "build_reb_aidstation_destroyhq"
    techrequirements = ['build_reb_triagecenter_destroyhq']

class OverrunRebelsAidStationInfo(RebelsAidStationInfo):
    name = "overrun_build_reb_aidstation"
    techrequirements = ['or_tier2_research']
    hidden = True