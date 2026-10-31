"""Roaming behavior system for Lambda Wars units.

Provides behavior system for units that roam the map and attack move
in random directions.
"""
from vmath import Vector
from navmesh import RandomNavAreaPosition, RandomNavAreaPositionWithin

def CreateBehaviorRoaming(BaseClass):
    """Create a roaming behavior class.
    
    Args:
        BaseClass: Base behavior class to inherit from.
        
    Returns:
        BehaviorRoaming: Roaming behavior class.
    """
    class BehaviorRoaming(BaseClass):
        """Behavior made for roaming enemies.
        
        They attack move into random directions, roaming the map.
        """
        def __init__(self, outer):
            """Initialize roaming behavior.
            
            Args:
                outer: Unit entity.
            """
            super().__init__(outer)

            self.start_roaming_time = gpGlobals.curtime

        class ActionIdle(BaseClass.ActionIdle):
            # Always chase enemies directly, otherwise might wait in unreachable positions
            idlewaitmoveuntilunderattack = False 

            def Update(self):
                behavior = self.behavior

                if gpGlobals.curtime - behavior.start_roaming_time > 150.0:
                    return self.SuspendFor(self.behavior.ActionAttackMove, 'Move attack enemy', RandomNavAreaPosition())

                origin = self.outer.GetAbsOrigin()
                radius = 1500
                hextent = Vector(radius, radius, 0.0)
                return self.SuspendFor(self.behavior.ActionAttackMove, 'Move attack enemy',
                                       RandomNavAreaPositionWithin(origin - hextent, origin + hextent))
            
    return BehaviorRoaming
