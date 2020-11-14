from vmath import Vector
from navmesh import RandomNavAreaPosition, RandomNavAreaPositionWithin

def CreateBehaviorRoaming(BaseClass):
    class BehaviorRoaming(BaseClass):
        def __init__(self, outer):
            super().__init__(outer)

            self.start_roaming_time = gpGlobals.curtime

        """ Behavior made for roaming enemies. They attack move into random directions, roaming the map. """
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
