"""Navigator classes for Lambda Wars units.

Provides navigation system for units to pathfind and move through the world.
"""
from unit_helper import UnitBaseNavigator, UnitBaseAirNavigator, UnitBasePath

class UnitCombatNavigator(UnitBaseNavigator):
    """Navigation system for ground combat units."""
    pass
    
class UnitCombatAirNavigator(UnitBaseAirNavigator):
    """Navigation system for air combat units."""
    pass
    