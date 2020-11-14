from core.buildings import UnitBaseBuilding, WarsBuildingInfo
from entities import entity, FOWFLAG_BUILDINGS_NEUTRAL_MASK
from srcbase import SOLID_BBOX
from vmath import Vector

class DotaBuildingInfo(WarsBuildingInfo):
    name = 'dota_building'
    displayname = 'Building'
    
class DotaBuildingFallBackInfo(DotaBuildingInfo):
    name = 'build_dota_unknown'
    displayname = 'Unknown Dota Building'
    attributes = []
    hidden = True

@entity('npc_dota_building', networked=True)
@entity('dota_building', networked=True)
@entity('ent_dota_fountain', networked=True)
class DotaBuilding(UnitBaseBuilding):
    fowflags = FOWFLAG_BUILDINGS_NEUTRAL_MASK
    buildingsolidmode = SOLID_BBOX
    
    def GetNavBlockBB(self):
        mins = Vector(self.unitinfo.mins)
        maxs = Vector(self.unitinfo.maxs)
        mins.z -= 64.0
        return mins, maxs
    
    def CreateVPhysics(self):
        return True
    
    def KeyValue(self, key, value):
        if key == 'unittype':
            return False
        if key == 'MapUnitName':
            self.SetUnitType(value)
            return True
        return super().KeyValue(key, value)
    
    def OnUnitTypeChanged(self, oldunittype):
        super().OnUnitTypeChanged(oldunittype)
        
        HealthBarOffset = getattr(self.unitinfo, 'HealthBarOffset', None)
        if HealthBarOffset:
            colprop = self.CollisionProp()
            self.barsoffsetz = HealthBarOffset - colprop.OBBMaxs().z
    
    def Spawn(self):
        self.constructionstate = self.BS_CONSTRUCTED
    
        super().Spawn()
        
        # In Dota 2, the team number is the owner
        self.SetOwnerNumber(self.GetTeamNumber())
        
    '''def SetConstructionState(self, state):
        super().SetConstructionState(state)
        
        unitinfo = self.unitinfo
        if unitinfo.mins:
            if unitinfo.mins.IsZero() and unitinfo.maxs.IsZero():
                UTIL_SetSize(self, self.WorldAlignMins(), self.WorldAlignMaxs())
            else:
                UTIL_SetSize(self, unitinfo.mins, unitinfo.maxs)'''

    unitinfofallback = DotaBuildingFallBackInfo
    unitinfovalidationcls = DotaBuildingInfo

    #selectionparticlename = 'unit_circle'
