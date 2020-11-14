from srcbase import IN_SPEED
from core.abilities import AbilityTargetGroup
if isserver:
    from core.units import BehaviorGeneric
    
if isserver:
    class ActionGarrisonBuilding(BehaviorGeneric.ActionAbility):
        def OnStart(self):
            return self.SuspendFor(ActionDoGarrisonBuilding, 'Moving in range', self.order.target)
            
        def OnEnd(self):
            # Make sure we are ungarrisoned when exiting this ability
            if self.outer.garrisoned_building:
                self.outer.garrisoned_building.UnGarrisonUnit(self.outer)
                
            # Give back movement control to locomotion component
            self.outer.aimoving = False
            
        def OnResume(self):
            outer = self.outer
            if outer.garrisoned:
                outer.navigator.StopMoving()
                outer.aimoving = False
                trans = self.CheckForEnemy()
                if trans:
                    return trans
            return super().OnResume()

        def Update(self):
            trans = self.CheckForEnemy()
            if trans:
                return trans

            return super().Update()

        def CheckForEnemy(self):
            outer = self.outer
            if not outer.garrisoned:
                return

            enemy = outer.garrisoned_building.GetEnemyForGarrisonedUnit(outer)
            if enemy:
                return self.SuspendFor(ActionGarrisonAttack, 'Enemy, lock on.', enemy)

    class ActionGarrisonAttack(BehaviorGeneric.ActionAttackNoMovement):
        def Update(self):
            # Move as close as possible to enemy
            outer = self.outer
            enemy = outer.garrisoned_building.GetEnemyForGarrisonedUnit(outer)
            #building = outer.garrisonbuilding
            #origin = outer.GetAbsOrigin()

            if not enemy or enemy != self.enemy:
                return self.Done('Lost enemy')
            
            """
            if building:
                buildingorigin = building.GetAbsOrigin()
                
                if enemy:
                    dir = enemy.GetAbsOrigin() - origin
                else:
                    dir = buildingorigin - origin
                VectorNormalize(dir)
 
                mins = Vector(); maxs = Vector()
                building.CollisionProp().WorldSpaceSurroundingBounds(mins, maxs)
                
                origin += dir * 100.0 * outer.think_freq
                origin.x = min(maxs.x, max(mins.x, origin.x))
                origin.y = min(maxs.y, max(mins.y, origin.y))
                origin.z = buildingorigin.z
                
                outer.SetAbsOrigin(origin)
            """
            return super().Update()
            
    class ActionDoGarrisonBuilding(BehaviorGeneric.ActionMoveTo):
        def Init(self, target, *args, **kwargs):
            super().Init(target, *args, **kwargs)
            
            self.target = target
            
        def OnNavComplete(self):
            target = self.target
            if target and target.CanGarrisonUnit(self.outer):
                target.GarrisonUnit(self.outer)
            return self.Done("NavComplete, moved to position")


class AbilityGarrison(AbilityTargetGroup):
    # Info
    name = "garrison"
    hidden = True
    
    @classmethod
    def OverrideOrder(cls, unit, data, player):
        ent = data.ent
        if not ent or not ent.IsUnit():
            return
    
        if not ent.garrisonable:
            return

        if ent.CanGarrisonUnit(unit):
            if isserver:
                unit.DoAbility(cls.name, [('leftpressed', data)], queueorder=player.buttons & IN_SPEED)
            return True
        return False
        
    # Ability
    if isserver:
        def DoAbility(self):
            data = self.mousedata
            target = data.ent

            for unit in self.units:
                unit.AbilityOrder(target=target, ability=self)
            self.Completed()
            
        behaviorgeneric_action = ActionGarrisonBuilding