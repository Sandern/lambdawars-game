"""Dummy building classes for Lambda Wars.

Provides dummy building entities used as placeholders or decorative elements
that can pass through damage and visibility to other entities.
"""
from srcbase import SOLID_NONE
from vmath import vec3_origin, vec3_angle
from entities import entity, DENSITY_GAUSSIAN
from .base import UnitBaseBuilding as BaseClass, WarsBuildingInfo
from fields import GetField, HasField

@entity('unit_dummy', networked=True)
class UnitDummy(BaseClass):
    """Dummy building entity that can pass through damage and visibility.
    
    Used as a placeholder or decorative element that forwards interactions
    to another entity.
    """
    if isserver:
        def Spawn(self):
            """Spawn the dummy building."""
            if self.unitinfo.decorative:
                self.buildingsolidmode = SOLID_NONE
        
            super().Spawn()
            
            if not self.unitinfo.decorative:
                self.SetUseCustomCanBeSeenCheck(True)
            else:
                self.SetCanBeSeen(False)
            
        def CustomCanBeSeen(self, unit=None):
            """Check if the dummy can be seen, forwarding to mouse pass entity.
            
            Args:
                unit: Unit checking visibility.
                
            Returns:
                bool: True if visible, False otherwise.
            """
            if self.GetMousePassEntity():
                return self.GetMousePassEntity().CanBeSeen(unit)
            return True

    def ConstructThink(self):
        """Dummy construction think (no-op)."""
        pass # Don't think

    def ConstructStep(self, intervalamount):
        """Dummy construction step (no-op).
        
        Args:
            intervalamount (float): Construction interval.
        """
        pass # Don't do steps
        
    def ClientThink(self):
        """Update client construction progress from mouse pass entity."""
        ent = self.GetMousePassEntity()
        if not ent:
            return
        
        # This will set the next client think time
        self.UpdateClientConstructionProgress(ent)

    # Damage
    def PassesDamageFilter(self, info):
        """Check if damage passes filter, forwarding to mouse pass entity.
        
        Args:
            info: Damage information.
            
        Returns:
            bool: True if damage passes filter, False otherwise.
        """
        if self.GetMousePassEntity():
            return self.GetMousePassEntity().PassesDamageFilter(info)
        return False
        
    def OnTakeDamage(self, info):
        """Handle damage, forwarding to mouse pass entity.
        
        Args:
            info: Damage information.
            
        Returns:
            int: Damage amount taken.
        """
        if self.GetMousePassEntity():
            return self.GetMousePassEntity().OnTakeDamage(info)   
        return 0
        
    # UI
    def ShowBars(self):
        """Show health/energy bars (no-op for dummies)."""
        pass
    def HideBars(self):
        """Hide health/energy bars (no-op for dummies)."""
        pass


class DummyInfo(WarsBuildingInfo):
    """Information class for dummy buildings."""
    cls_name = 'unit_dummy'
    hidden = True
    minimaphalfwide = 0
    minimaphalftall = 0
    ispriobuilding = False # Does not need to be destroyed to win the game
    sai_hint = set() # Hints should go on main building
    decorative = False
    
    dummyinfo = {}


def CreateDummy(offset=vec3_origin, angle=vec3_angle, blocknavareas=True, blockdensitytype=DENSITY_GAUSSIAN, **kwargs):
    """Create a new dummy building info class.
    
    Args:
        offset (Vector): Offset position for the dummy.
        angle (QAngle): Rotation angle for the dummy.
        blocknavareas (bool): Whether to block navigation areas.
        blockdensitytype: Density type for navigation blocking.
        **kwargs: Additional properties to set on the dummy info.
        
    Returns:
        DummyInfo: New dummy info class.
    """
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