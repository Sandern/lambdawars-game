"""Object unit classes for Lambda Wars.

Provides base classes for object "units" that don't behave like real units,
such as projectiles, explosives, and scrap.
"""
from .base import UnitBase as BaseClass, UnitInfo
from entities import networked

class UnitObjectInfo(UnitInfo):
    """Information class for object units.
    
    Objects default to not being visible on the minimap and don't take population.
    """
    # Objects default to not being visible on the minimap
    minimaphalfwide = 0
    minimaphalftall = 0
    
    # No hints for strategic AI
    sai_hint = set([])
    
    # No population
    population = 0

@networked
class UnitBaseObject(BaseClass):
    """Base class for object "units".
    
    These are derived from the unit code, but don't behave like real units.
    Examples are projectiles, explosives, scrap, etc.
    """
    def GetIMouse(self):
        """Get mouse interface (returns None for objects).
        
        Returns:
            None: Objects don't have a mouse interface.
        """
        return None
        
    def IsSelectableByPlayer(self, player, target_selection):
        """Check if object is selectable by player.
        
        Args:
            player: Player entity.
            target_selection: Target selection type.
            
        Returns:
            bool: False, objects are not selectable.
        """
        return False
        
    unitinfo = UnitObjectInfo
    unitinfofallback = UnitObjectInfo
    unitinfovalidationcls = UnitObjectInfo # unitinfo should be of this type, otherwise fallback will be used!
