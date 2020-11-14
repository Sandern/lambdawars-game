from .base import UnitBase as BaseClass, UnitInfo
from entities import networked

class UnitObjectInfo(UnitInfo):
    # Objects default to not being visible on the minimap
    minimaphalfwide = 0
    minimaphalftall = 0
    
    # No hints for strategic AI
    sai_hint = set([])
    
    # No population
    population = 0

@networked
class UnitBaseObject(BaseClass):
    ''' Serves as a base for object "units".
        These are derived from the unit code, but don't behave like a real units.
        
        Examples are projectiles, explosives, scrap, etc
    '''
    def GetIMouse(self):
        ''' Returns if this entity has a mouse interface.
            By default units have this, but return None to prevent this.
        '''
        return None
        
    def IsSelectableByPlayer(self, player, target_selection):
        return False
        
    unitinfo = UnitObjectInfo
    unitinfofallback = UnitObjectInfo
    unitinfovalidationcls = UnitObjectInfo # unitinfo should be of this type, otherwise fallback will be used!
