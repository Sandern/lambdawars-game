from srcbase import IN_SPEED
from .target import AbilityTargetGroup
from core.units.orders import GroupMoveOrder


class GroupPatrolAttackMove(GroupMoveOrder):
    def ExecuteUnitForPosition(self, unit, target_pos):
        data = self.player.GetMouseData()
        target = None
        if unit.IsValidEnemy(data.ent):
            target = data.ent
        
        # NOTE: we do the clear orders check here already so we first check if the last order is a patrol order
        createstartpoint = True
        insertidx = None # None for append to back
        if self.player and not (self.player.buttons & IN_SPEED):
            unit.ClearAllOrders(notifyclient=False, dispatchevent=False)
        elif unit.orders:
            # Have orders, check if last appended order is patrol
            createstartpoint = False
            lastorder = unit.orders[-1]
            lastability = lastorder.ability
            if lastability and lastability.name == self.ability.name:
                insertidx = unit.orders.index(lastorder)
        
        if createstartpoint:
            # Insert start location
            unit.AbilityOrder(position=unit.GetAbsOrigin(),
                              ability=self.ability,
                              repeat=True, alwaysqueue=True)
        
        # Add the new patrol point
        unit.AbilityOrder(idx=insertidx, target=target,
                          position=target_pos,
                          ability=self.ability,
                          repeat=True, alwaysqueue=True)
                    

class AbilityPatrol(AbilityTargetGroup):
    # Info
    name = "patrol"
    image_name = 'vgui/abilities/patrol.vmt'
    displayname = "#AbilityPatrol_Name"
    description = "#AbilityPatrol_Description"
    hidden = True
    #activatesoundscript = '#patrol'
    activatesoundscript_force_play = False
    allowcontinueability = True
    cloakallowed = True
    
    def AllowAutoCast(self, unit):
        return True
    
    # Ability
    def DoAbility(self):
        if isserver:
            from core.units import BehaviorGeneric # FIXME
            self.behaviorgeneric_action = BehaviorGeneric.ActionAbilityAttackMove

        patrolattackmove = GroupPatrolAttackMove(self.player, self.targetpos, self.units)
        patrolattackmove.ability = self
        patrolattackmove.Apply()
        
        if isserver:
            self.Completed()
