from vmath import VectorNormalize, Vector
from core.abilities import AbilityTarget, AbilityUpgrade
from entities import FClassnameIs

if isserver:
    from core.units import BehaviorGeneric
    from entities import D_LI
    
    # Actions
    class ActionDoShootWinchester(BehaviorGeneric.ActionAbility):
        def OnStart(self):
            return self.SuspendFor(ActionShootWinchester, 'Shooting', self.order, self)
            
        def OnResume(self):
            self.changetoidleonlostorder = True
            if self.outer.curorder == self.order:
                self.order.Remove(dispatchevent=False)
            return super().OnResume()
            
        def OnEnd(self):
            super().OnEnd()
            
            if not self.order.ability.stopped:
                self.order.ability.Cancel()

    class ActionShootWinchester(BehaviorGeneric.ActionMoveInRangeAndFace):
        def Init(self, order, parent_action):
            target = order.target if order.target else order.position
            
            super().Init(target, 1024.0)

            self.parent_action = parent_action
            self.ability = order.ability
            
        def Update(self):
            ability = self.ability
            if not self.target:
                ability.Cancel()
                return self.Done('Lost target')
            if not ability.CanDoAbility(ability.player, self.outer):
                ability.Cancel()
                return self.Done('Can no longer do ability')
            return super().Update()
            
        def OnInRangeAndFacing(self):
            outer = self.outer
            ability = self.ability

            if not ability.CanDoAbility(ability.player, outer):
                ability.Cancel()
                return self.Done('Can no longer do ability')

            ability.SetNotInterruptible()
            duration = 0.5
            outer.activeweapon.SecondaryAttack(duration)
            outer.DoAnimation(outer.ANIM_ATTACK_SECONDARY)
            ability.SetRecharge(outer)
            ability.Completed()
            self.parent_action.changetoidleonlostorder = False
            return self.ChangeTo(self.behavior.ActionLockAim, 'Fired cannon', self.target, duration=duration)


class WinchesterAltFire(AbilityTarget):
    # Info
    name = "winchester_alt_fire"
    displayname = '#AbilityWinchesterShot_Name'
    description = '#AbilityWinchesterShot_Description'
    image_name = 'vgui/rebels/abilities/winchester_alt_fire'
    #costs = []
    #rechargetime = 2
    techrequirements = []
    #sai_hint = AbilityTarget.sai_hint | set(['sai_combine_ball'])

    # Ability
    if isserver:
        def DoAbility(self):
            data = self.mousedata
            
                
            if not self.TakeResources(refundoncancel=True):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return

            target = data.ent if (data.ent and not data.ent.IsWorld()) else None
            if not target:
                self.Cancel(cancelmsg='#Ability_InvalidTarget')
                return
            if target.IRelationType(self.unit) == D_LI:
                self.Cancel(cancelmsg='#Ability_InvalidTarget')
                return
            self.unit.AbilityOrder(ability=self, target=target, position=data.endpos)

        behaviorgeneric_action = ActionDoShootWinchester
        
    @classmethod    
    def GetRequirements(info, player, unit):
        requirements = set()
        activeweapon = unit.activeweapon
        if not activeweapon or not FClassnameIs(activeweapon, 'weapon_winchester1886'):
            requirements.add('requirewinchester')
        return requirements | super().GetRequirements(player, unit)
        
    @classmethod    
    def ShouldShowAbility(info, unit):
        activeweapon = unit.activeweapon
        if not activeweapon or not FClassnameIs(activeweapon, 'weapon_winchester1886'):
            return False
        return super().ShouldShowAbility(unit)