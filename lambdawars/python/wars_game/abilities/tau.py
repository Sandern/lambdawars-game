from vmath import VectorNormalize, Vector
from core.abilities import AbilityTarget, AbilityUpgrade
from entities import FClassnameIs

if isserver:
    from core.units import BehaviorGeneric
    from entities import D_LI
    
    # Actions
    class ActionDoShootTau(BehaviorGeneric.ActionAbility):
        def OnStart(self):
            return self.SuspendFor(ActionShootTau, 'Shooting ball', self.order, self)
            
        def OnResume(self):
            self.changetoidleonlostorder = True
            if self.outer.curorder == self.order:
                self.order.Remove(dispatchevent=False)
            return super().OnResume()
            
        def OnEnd(self):
            super().OnEnd()
            
            if not self.order.ability.stopped:
                self.order.ability.Cancel()

    class ActionShootTau(BehaviorGeneric.ActionMoveInRangeAndFace):
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
            duration = 1.1
            outer.activeweapon.SecondaryAttack(self.target.GetAbsOrigin(), ability.damage, ability.damageradius, duration, self.target)
            outer.DoAnimation(outer.ANIM_ATTACK_SECONDARY)
            ability.SetRecharge(outer)
            ability.Completed()
            self.parent_action.changetoidleonlostorder = False
            return self.ChangeTo(self.behavior.ActionLockAim, 'Fired cannon', self.target, duration=duration)


class TauAltFire(AbilityTarget):
    # Info
    name = "tau_alt_fire"
    displayname = '#AbilityTauAltShot_Name'
    description = '#AbilityTauAltShot_Description'
    image_name = 'vgui/rebels/abilities/ability_tau_alt_fire'
    #costs = []
    rechargetime = 60
    techrequirements = ['tau_alt_fire_unlock']
    damage = 400
    damageradius = 64
    sai_hint = AbilityTarget.sai_hint | set(['sai_combine_ball'])

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
            if target.isbuilding:
                self.Cancel(cancelmsg='#Ability_InvalidTarget')
                return
            self.unit.AbilityOrder(ability=self, target=target, position=data.endpos)

        behaviorgeneric_action = ActionDoShootTau
        
    @classmethod    
    def GetRequirements(info, player, unit):
        requirements = set()
        activeweapon = unit.activeweapon
        if not activeweapon or not FClassnameIs(activeweapon, 'weapon_tau'):
            requirements.add('requiretau')
        return requirements | super().GetRequirements(player, unit)
        
    @classmethod    
    def ShouldShowAbility(info, unit):
        activeweapon = unit.activeweapon
        if not activeweapon or not FClassnameIs(activeweapon, 'weapon_tau'):
            return False
        return super().ShouldShowAbility(unit)
class OverrunTauAltFire(TauAltFire):
    name = "overrun_tau_alt_fire"
    costs = []
    rechargetime = 60
    techrequirements = []
    #damage = 200
    #damageradius = 32
class AbilityTauAltFireUnlock(AbilityUpgrade):
    name = 'tau_alt_fire_unlock'
    displayname = '#AbilityTauAltShotUnlock_Name'
    description = '#AbilityTauAltShotUnlock_Description'
    image_name = "vgui/rebels/abilities/tau_alt_unlock"
    #techrequirements = ['build_comb_specialops']
    buildtime = 75.0
    costs = [[('kills', 5)], [('requisition', 50), ('scrap', 75)]]