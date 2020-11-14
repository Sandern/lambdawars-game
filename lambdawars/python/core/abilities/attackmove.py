from .target import AbilityTargetGroup
from core.units.orders import GroupMoveOrder


class GroupAttackMove(GroupMoveOrder):
    def ExecuteUnitForPosition(self, unit, target_pos):
        data = self.player.GetMouseData()
        ent = data.ent
        target = None
        if ent and (ent.IsUnit() or ent.health > 0):
            target = ent
            
        unit.AbilityOrder(target=target,
                          position=target_pos,
                          ability=self.ability)


class AbilityAttackMove(AbilityTargetGroup):
    # Info
    name = "attackmove"
    image_name = 'vgui/abilities/attackmove.vmt'
    rechargetime = 0
    displayname = "#AbilityAttackMove_Name"
    description = "#AbilityAttackMove_Description"
    hidden = True
    activatesoundscript = '#attackmove'
    activatesoundscript_force_play = False
    allowcontinueability = True
    cloakallowed = True
    rallylinemat = 'vgui/rallyline_attack'
    
    def AllowAutoCast(self, unit):
        return True
    
    # Ability
    def DoAbility(self):
        if isserver:
            from core.units import BehaviorGeneric  # FIXME
            self.behaviorgeneric_action = BehaviorGeneric.ActionAbilityAttackMove

        attackmove = GroupAttackMove(self.player, self.targetpos, self.units)
        attackmove.ability = self
        attackmove.Apply()
        
        if isserver:
            self.Completed()
