from srcbase import SOLID_NONE
from vmath import vec3_origin, vec3_angle
from entities import entity, DENSITY_GAUSSIAN
from .base import UnitBaseBuilding as BaseClass, WarsBuildingInfo
from fields import GetField, HasField

@entity('unit_dummy', networked=True)
class UnitDummy(BaseClass):
    if isserver:
        def Spawn(self):
            if self.unitinfo.decorative:
                self.buildingsolidmode = SOLID_NONE
        
            super().Spawn()
            
            if not self.unitinfo.decorative:
                self.SetUseCustomCanBeSeenCheck(True)
            else:
                self.SetCanBeSeen(False)
            
        def CustomCanBeSeen(self, unit=None):
            if self.GetMousePassEntity():
                return self.GetMousePassEntity().CanBeSeen(unit)
            return True

    def ConstructThink(self):
        pass # Don't think

    def ConstructStep(self, intervalamount):
        pass # Don't do steps
        
    def ClientThink(self):
        ent = self.GetMousePassEntity()
        if not ent:
            return
        
        # This will set the next client think time
        self.UpdateClientConstructionProgress(ent)

    # Damage
    def PassesDamageFilter(self, info):
        if self.GetMousePassEntity():
            return self.GetMousePassEntity().PassesDamageFilter(info)
        return False
        
    def OnTakeDamage(self, info):
        if self.GetMousePassEntity():
            return self.GetMousePassEntity().OnTakeDamage(info)   
        return 0
        
    # UI
    def ShowBars(self):
        pass
    def HideBars(self):
        pass


class DummyInfo(WarsBuildingInfo):
    cls_name = 'unit_dummy'
    hidden = True
    minimaphalfwide = 0
    minimaphalftall = 0
    ispriobuilding = False # Does not need to be destroyed to win the game
    sai_hint = set() # Hints should go on main building
    decorative = False
    
    dummyinfo = {}


def CreateDummy(offset=vec3_origin, angle=vec3_angle, blocknavareas=True, blockdensitytype=DENSITY_GAUSSIAN, **kwargs):
    # Create new dummy info
    class NewDummyInfoInternal(DummyInfo):
        cls_name = 'unit_dummy'
        hidden = True
        dummyinfo = {
            'offset': offset,
            'angle': angle,
            'blocknavareas': blocknavareas,
            'blockdensitytype': blockdensitytype,
        }
        
    # Dynamic part
    for k, v in kwargs.items():
        if HasField(NewDummyInfoInternal, k):
            field = GetField(NewDummyInfoInternal, k)
            field.Set(NewDummyInfoInternal, v)
            field.default = v
        else:
            setattr(NewDummyInfoInternal, k, v)
        
    return NewDummyInfoInternal