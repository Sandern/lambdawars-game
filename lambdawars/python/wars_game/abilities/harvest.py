from srcbase import DMG_GENERIC, IN_SPEED
from core.abilities import AbilityTargetGroup
if isserver:
    from core.units import BaseBehavior
    from entities import gEntList
    
if isserver:
    class ActionHarvest(BaseBehavior.ActionAbility):
        def FindNearest(self, classname):
            cur = gEntList.FindEntityByClassname(None, classname)
            if not cur:
                return None
            best = None
            while cur:
                if cur.GetOwnerNumber() == self.outer.GetOwnerNumber():
                    dist = cur.GetAbsOrigin().DistTo(self.outer.GetAbsOrigin())
                    if not best:
                        best = cur
                        bestdist = dist
                    else:
                        if dist < bestdist:
                            best = cur
                            bestdist = dist
                cur = gEntList.FindEntityByClassname(cur, classname)
            return best
            
        def FindNearestColony(self): return self.FindNearest("build_ant_colony")
        def FindNearestPheromoneMarker(self): return self.FindNearest("pheromone_marker")
            
        def Update(self):
            p = self.order.target
            
            dist = (p.GetLocalOrigin() - self.outer.GetLocalOrigin()).Length2D()
            if not self.outer.carryinggrub and (dist > self.MINRANGE_MARKER+self.TOLERANCE+1.0):
                return self.SuspendFor(self.behavior.ActionMoveInRange, "Moving to pheromone marker", p, maxrange=self.MINRANGE_MARKER, tolerance=self.TOLERANCE)
            elif not self.outer.carryinggrub:
                grub = self.outer.assignedgrub if self.outer.assignedgrub else p.GetFreeGrub(self.outer)
                if grub:
                    self.outer.assignedgrub = grub
                    grub.Get().assignedtoworker = self.outer.GetHandle()
                    return self.SuspendFor(self.behavior.ActionMoveTo, "Picking up a grub", grub, tolerance=self.TOLERANCE)
            else:
                nearestcolony = self.FindNearestColony()
                if not nearestcolony:
                    return self.ChangeTo(self.behavior.ActionIdle, "No colony to return to...")
                return self.SuspendFor(self.behavior.ActionMoveInRange, "Moving to colony with a grub on my back", nearestcolony, maxrange=self.MINRANGE_COLONY, tolerance=self.TOLERANCE)
            
            return self.Continue()
            
        def OnEnd(self):
            if self.outer.assignedgrub:
                self.outer.assignedgrub.Get().assignedtoworker = None
                self.outer.assignedgrub = None
            super().OnEnd()
            
        def OnResume(self):
            if self.outer.carryinggrub:
                nearestcolony = self.FindNearestColony()
                if nearestcolony and self.outer.GetAbsOrigin().DistTo(nearestcolony.GetAbsOrigin()) < self.MINRANGE_COLONY+self.TOLERANCE+1.0:
                    self.outer.carryinggrub.SetParent(None)
                    nearestcolony.AddExistingGrub( self.outer.carryinggrub )   
                    self.outer.carryinggrub = None
                    self.outer.assignedgrub = None
                    
        MINRANGE_COLONY = 340.0 # Minimum range required to deliver a grub to the colony
        MINRANGE_MARKER = 512.0 # Minimum range until we get a grub assigned. After that the worker moves to the exact spot.
        TOLERANCE = 32.0
        
class AbilityHarvest(AbilityTargetGroup):
    # Info
    name = "harvest"
    image_name = 'vgui/abilities/collectgrubs.vmt'
    rechargetime = 0
    displayname = "#AbilityHarvest_Name"
    description = "#AbilityHarvest_Description"
    hidden = True
    
    @classmethod
    def OverrideOrder(cls, unit, data, player):
        if isserver: # TODO: client
            if data.ent and data.ent.IsUnit():
                if (data.ent.ClassMatches('pheromone_marker') or 
                        (data.ent.ClassMatches('build_ant_colony') and 
                         data.ent.GetOwnerNumber() == unit.GetOwnerNumber())):
                    unit.DoAbility('harvest', [('leftpressed', data)], queueorder=player.buttons & IN_SPEED)
                    return True
        return False
        
    # Ability
    if isserver:
        def DoAbility(self):
            data = self.mousedata
            target = data.ent
            if not target or target.IsWorld():
                self.Cancel(cancelmsg='#Ability_InvalidTarget')
                return
            
            for unit in self.units:
                if (not target.ClassMatches('pheromone_marker') and
                        not (target.ClassMatches('build_ant_colony') and unit.carryinggrub)):
                    continue
                unit.AbilityOrder(target=target, ability=self)
            self.Completed()
            
        behaviorgeneric_action = ActionHarvest
